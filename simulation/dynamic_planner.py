import numpy as np
import heapq
try:
    from simulation.default_configuration_simulation import (
        GRID_SIZE, GRID_RESOLUTION, PROXEMIC_BUFFER)
except ModuleNotFoundError:
    from default_configuration import (
        GRID_SIZE, GRID_RESOLUTION, PROXEMIC_BUFFER)

from simulation.perception import PerceptionModule

class DynamicNavigator:
    """
    A* on a binary occupancy grid built from PerceptionModule.dynamic_semantic_map,
    with continuous replanning when new obstacles appear.
    """
    def __init__(self):
        self.grid_size = GRID_SIZE 
        self.resolution = GRID_RESOLUTION 
        self.buffer = PROXEMIC_BUFFER 
        self.perceptor = PerceptionModule()

    def world_to_grid(self, x, y):
        center = self.grid_size // 2
        i = int(round(x / self.resolution)) + center
        j = int(round(y / self.resolution)) + center
        return i, j

    def build_occupancy_grid(self):
        grid = np.zeros((self.grid_size, self.grid_size), dtype=np.uint8)
        sem_map = self.perceptor.get_dynamic_semantic_map()
        pad = int(self.buffer / self.resolution)
        for label, x, y, _ in sem_map:
            ci, cj = self.world_to_grid(x, y)
            for di in range(-pad, pad+1):
                for dj in range(-pad, pad+1):
                    ni, nj = ci+di, cj+dj
                    if 0 <= ni < self.grid_size and 0 <= nj < self.grid_size:
                        if di*di + dj*dj <= pad*pad:
                            grid[ni, nj] = 1
        return grid

    def heuristic(self, a, b):
        return np.hypot(a[0]-b[0], a[1]-b[1])

    def a_star(self, grid, start, goal):
        neighbors = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
        open_set = [(0 + self.heuristic(start, goal), 0, start, None)]
        came_from, g_score = {}, {start: 0}

        while open_set:
            f, g, current, parent = heapq.heappop(open_set)
            if current in came_from:
                continue
            came_from[current] = parent
            if current == goal:
                break
            for dx, dy in neighbors:
                nb = (current[0]+dx, current[1]+dy)
                if (0 <= nb[0] < self.grid_size and
                    0 <= nb[1] < self.grid_size and
                    grid[nb] == 0):
                    tentative_g = g + self.heuristic((0,0),(dx,dy))
                    if tentative_g < g_score.get(nb, np.inf):
                        g_score[nb] = tentative_g
                        heapq.heappush(open_set, (
                            tentative_g + self.heuristic(nb, goal),
                            tentative_g, nb, current
                        ))
        if goal not in came_from:
            return None
        # reconstruct
        path, node = [], goal
        while node:
            path.append(node)
            node = came_from[node]
        return list(reversed(path))

    def navigate(self, start_xy, goal_xy, move_callback, check_callback):
        """
        Loop: build grid → A* → follow path cell-by-cell with move_callback().
        If any cell becomes occupied, break and replan.
        """
        goal_cell = self.world_to_grid(*goal_xy)
        current_xy = start_xy

        while True:
            start_cell = self.world_to_grid(*current_xy)
            grid = self.build_occupancy_grid()
            path = self.a_star(grid, start_cell, goal_cell)
            if not path:
                raise RuntimeError("No path found.")
            for cell in path[1:]:
                if cell == goal_cell:
                    return
                if self.build_occupancy_grid()[cell] == 1:
                    break
                x = (cell[0] - self.grid_size//2) * self.resolution
                y = (cell[1] - self.grid_size//2) * self.resolution
                move_callback(x, y)
                current_xy = check_callback()
            else:
                return


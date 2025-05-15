import pybullet as p
import heapq
import math
import time

def obstacles_grid(ground_plane_id, pepper_id, grid_size):
    grid = [[0 for _ in range(grid_size[1])] for _ in range(grid_size[0])]

    for obstacle_id in range(p.getNumBodies()):
        if (pepper_id is not None and obstacle_id == pepper_id) or (ground_plane_id is not None and obstacle_id == ground_plane_id):
            continue

        aabb_min, aabb_max = p.getAABB(obstacle_id)

        if aabb_min[2] > 1.0:
            continue

        try:
            min_i, min_j = aabb_min[0], aabb_min[1]
            max_i, max_j = aabb_max[0], aabb_max[1]
        except Exception as e:
            print(f"Error in obstacles_grid: {e}")
            continue

        for i in range(int(min_i), int(max_i + 1)):
            for j in range(int(min_j), int(max_j + 1)):
                if 0 <= i < grid_size[0] and 0 <= j < grid_size[1]:
                    grid[i][j] = 1

    return grid

def A_star_algorithm(p_start_r, p_goal_r, grid):

    def inside_grid_and_not_obstacle(p):
        i, j = p
        return (0 <= i < len(grid) and 0 <= j < len(grid[0])) and grid[i][j] == 0

    def heuristic(x_0, x_1):
        #euclidean distance
        return math.hypot(x_1[0] - x_0[0], x_1[1] - x_0[1])

    def getNeighbors(p):
        i, j = p
        dir = [(-1,0), (1,0), (0,-1), (0,1)]
        n = [(i+i2, j+j2) for i2, j2 in dir]
        return [k for k in n if inside_grid_and_not_obstacle(k)]

    open_set = []
    previous = {}
    heapq.heappush(open_set, (0, p_start_r))
    g_s = {p_start_r: 0}
    f_s = {p_start_r: heuristic(p_start_r, p_goal_r)}

    while open_set:

        _, x = heapq.heappop(open_set)

        if x == p_goal_r:
            path = [x]

            while x in previous:
                x = previous[x]
                path.append(x)
            return list(reversed(path))

        for n in getNeighbors(x):

            g = g_s[x] + 1

            if n not in g_s or g < g_s[n]:
                previous[n] = x
                g_s[n] = g
                f_s[n] = g + heuristic(n, p_goal_r)
                heapq.heappush(open_set, (f_s[n], n))

    return None

def moveToGoal(pepper, path):
    for x_goal, y_goal in path:
        p_start = pepper.getPosition()

        x_curr = round(p_start[0])
        y_curr = round(p_start[1])

        delta_x = x_goal - x_curr
        delta_y = y_goal - y_curr
        delta_theta = math.atan2(delta_y, delta_x)

        print(f"Move: from ({x_curr}, {y_curr}) to ({x_goal}, {y_goal}) with theta = {delta_theta} rad")

        pepper.moveTo(0, 0, delta_theta)
        time.sleep(0.5)

        distance = math.hypot(delta_x, delta_y)
        pepper.moveTo(distance, 0, 0)
        time.sleep(0.5)



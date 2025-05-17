import pybullet as p
import heapq
import math
import time

import useful_functions

def world_to_grid(x, y, grid_size, cell_size):
    x_offset = grid_size[0] // 2
    y_offset = grid_size[1] // 2
    return int((x / cell_size) + x_offset), int((y / cell_size) + y_offset)

def grid_to_world(x_g, y_g, grid_size, cell_size):
    x_offset = grid_size[0] // 2
    y_offset = grid_size[1] // 2
    return (x_g - x_offset)*cell_size, (y_g - y_offset)*cell_size

def obstacles_grid(ground_plane_id, pepper_id, grid_size, cell_size, ignored_ids=None):

    if ignored_ids is None:
        ignored_ids = []

    grid = [[0 for _ in range(grid_size[1])] for _ in range(grid_size[0])]

    for obstacle_id in range(p.getNumBodies()):
        if obstacle_id in ignored_ids:
            continue
        if (pepper_id is not None and obstacle_id == pepper_id) or (ground_plane_id is not None and obstacle_id == ground_plane_id):
            continue

        aabb_min, aabb_max = p.getAABB(obstacle_id)

        try:
            min_x, min_y = aabb_min[0], aabb_min[1]
            max_x, max_y = aabb_max[0], aabb_max[1]
        except Exception as e:
            print(f"Error in obstacles_grid: {e}")
            continue

        x = min_x
        while x <= max_x:
            y = min_y
            while y <= max_y:
                x_g, y_g = world_to_grid(x, y, grid_size, cell_size)
                if 0 <= x_g < grid_size[0] and 0 <= y_g < grid_size[1]:

                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            x_g2, y_g2 = x_g + dx, y_g + dy
                            if 0 <= x_g2 < grid_size[0] and 0 <= y_g2 < grid_size[1]:
                                grid[x_g2][y_g2] = 1
                y += cell_size / 2
            x += cell_size / 2

    return grid

def A_star_algorithm(p_start_g, p_goal_g, grid):

    def inside_grid_and_not_obstacle(p):
        i, j = p
        return (0 <= i < len(grid) and 0 <= j < len(grid[0])) and grid[i][j] == 0

    def heuristic(x_0, x_1):
        #euclidean dist
        return math.hypot(x_1[0] - x_0[0], x_1[1] - x_0[1])

    def getNeighbors(p):
        i, j = p
        dirs = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]
        neighbors = [(i+di, j+dj) for di, dj in dirs]
        return [k for k in neighbors if inside_grid_and_not_obstacle(k)]


    open_set = []
    previous = {}
    heapq.heappush(open_set, (0, p_start_g))
    g_s = {p_start_g: 0}
    f_s = {p_start_g: heuristic(p_start_g, p_goal_g)}

    while open_set:

        _, x = heapq.heappop(open_set)

        if x == p_goal_g:
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
                f_s[n] = g + heuristic(n, p_goal_g)
                heapq.heappush(open_set, (f_s[n], n))

    return None

def checkObstacles(pepper, dist_threshold = 0.5):

    position, th = p.getBasePositionAndOrientation(pepper.robot_model)
    yaw = p.getEulerFromQuaternion(th)[2]

    dx = math.cos(yaw)
    dy = math.sin(yaw)

    from_position = position
    to_position = (position[0] + dx * dist_threshold, position[1] + dy * dist_threshold, position[2])

    hit = p.rayTest(from_position, to_position)[0]

    return hit[0] != -1 and hit[2] < 1


def move(pepper, path):
    
    _, th = p.getBasePositionAndOrientation(pepper.robot_model)
    theta = p.getEulerFromQuaternion(th)[2]

    for i in range(len(path) - 1):
        x, y = path[i]
        x_new, y_new = path[i + 1]

        delta_x = x_new - x
        delta_y = y_new - y

        theta_new = math.atan2(delta_y, delta_x)
        delta_theta = theta_new - theta
        delta_theta = (delta_theta + math.pi) % (2 * math.pi) - math.pi

        if abs(delta_theta) > 1e-2:
            pepper.moveTo(0, 0, delta_theta)
            time.sleep(0.5)
            theta = theta_new

        if checkObstacles(pepper):
            print("Detected obstacle, movement ended")
            return False

        print(f"Movement: from ({x}, {y}) to ({x_new}, {y_new})")
        dist = math.hypot(delta_x, delta_y)
        pepper.moveTo(dist, 0, 0)
        time.sleep(0.5)

    return True

def correction(pepper, goal, threshold=0.0001):
    current_pos = pepper.getPosition()
    dx = goal[0] - current_pos[0]
    dy = goal[1] - current_pos[1]
    dist = math.hypot(dx, dy)

    if dist > threshold:
        print(f"Application of correction ({dist:.2f} m)")

        theta_new = math.atan2(dy, dx)
        _, th = p.getBasePositionAndOrientation(pepper.robot_model)
        theta = p.getEulerFromQuaternion(th)[2]

        delta_theta = theta_new - theta
        delta_theta = (delta_theta + math.pi) % (2 * math.pi) - math.pi

        if abs(delta_theta) > 1e-2:
            pepper.moveTo(0, 0, delta_theta)
            time.sleep(0.3)

        pepper.moveTo(dist, 0, 0)
        time.sleep(0.5)
        print("Correct Pepper goal position reaches")

def moveToGoal(pepper, p_goal, ignored_ids):

    ground_plane_id = useful_functions.getGroundPlane_id()
    pepper_id = pepper.robot_model
    grid_size = (64, 64)
    cell_size = 0.25

    grid = obstacles_grid(ground_plane_id, pepper_id, grid_size, cell_size, ignored_ids)

    position = pepper.getPosition()

    p_start = (useful_functions.round_cell_size(position[0]), useful_functions.round_cell_size(position[1]))

    p_start_g = world_to_grid(p_start[0], p_start[1], grid_size, cell_size)
    p_goal_g = world_to_grid(p_goal[0], p_goal[1], grid_size, cell_size)

    useful_functions.print_grid_created(grid, p_start_g, p_goal_g)

    p_start_w = grid_to_world(p_start_g[0], p_start_g[1], grid_size, cell_size)
    p_goal_w = grid_to_world(p_goal_g[0], p_goal_g[1], grid_size, cell_size)

    print(f"Start position: {p_start} and goal position: {p_goal}")

    path_grid = A_star_algorithm(p_start_g, p_goal_g, grid)

    if path_grid:
        path_world = [grid_to_world(x_g, y_g, grid_size, cell_size) for (x_g, y_g) in path_grid]

        print(f"Path found: {path_world}")

        if move(pepper, path_world):

            print(pepper.getPosition())
            time.sleep(2)

            correction(pepper, p_goal)

            print(f"Goal reached: {p_goal}")
            print("Pepper position:", pepper.getPosition())

        print("Pepper position:", pepper.getPosition())


        time.sleep(2)

    else:
        print("Path not found")
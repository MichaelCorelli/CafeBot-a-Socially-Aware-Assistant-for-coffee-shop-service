import pybullet as p
import heapq
import math
import time

from . import useful_functions

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

                    for delta_x in [-1, 0, 1]:
                        for delta_y in [-1, 0, 1]:
                            x_g2, y_g2 = x_g + delta_x, y_g + delta_y
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

def checkObstacles(pepper, dist_threshold = 1.3):

    position, th = p.getBasePositionAndOrientation(pepper.robot_model)
    yaw = p.getEulerFromQuaternion(th)[2]

    delta_x = math.cos(yaw)
    delta_y = math.sin(yaw)

    from_position = position
    to_position = (position[0] + delta_x * dist_threshold, position[1] + delta_y * dist_threshold, position[2])

    hit = p.rayTest(from_position, to_position)[0]

    return hit[0] != -1 and hit[2] < 1

def move(pepper, path, pepper_positions=None, path_positions=None, errors=None):
    
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

        if pepper_positions is not None and path_positions is not None and errors is not None:
            pos = pepper.getPosition()
            pepper_positions.append((pos[0], pos[1]))
            path_positions.append((x_new, y_new))
            error = math.hypot(x_new - pos[0], y_new - pos[1])
            errors.append(error)

    return True

def correction(pepper, p_goal, threshold=0.0001, pepper_positions=None, path_positions=None, errors=None):
    position = pepper.getPosition()
    delta_x = p_goal[0] - position[0]
    delta_y = p_goal[1] - position[1]
    dist = math.hypot(delta_x, delta_y)

    if dist > threshold:
        print(f"Applying correction: distance = {dist:.3f}")

        theta_new = math.atan2(delta_y, delta_x)
        _, th = p.getBasePositionAndOrientation(pepper.robot_model)
        theta = p.getEulerFromQuaternion(th)[2]

        delta_theta = theta_new - theta
        delta_theta = (delta_theta + math.pi) % (2 * math.pi) - math.pi

        if abs(delta_theta) > 1e-2:
            pepper.moveTo(0, 0, delta_theta)
            time.sleep(0.3)

        pepper.moveTo(dist, 0, 0)
        time.sleep(0.5)

        if pepper_positions is not None and path_positions is not None and errors is not None:
            pos = pepper.getPosition()
            pepper_positions.append((pos[0], pos[1]))
            path_positions.append((p_goal[0], p_goal[1]))
            error = math.hypot(p_goal[0] - pos[0], p_goal[1] - pos[1])
            errors.append(error)

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

    print(f"Start position: {p_start} and goal position: {p_goal}")

    path_grid = A_star_algorithm(p_start_g, p_goal_g, grid)

    if path_grid:
        path_world = [grid_to_world(x_g, y_g, grid_size, cell_size) for (x_g, y_g) in path_grid]
        print(f"Path found: {path_world}")

        pepper_positions = []
        path_positions = []
        errors = []

        if move(pepper, path_world, pepper_positions, path_positions, errors):
            print("Position before correction:", pepper.getPosition())
            time.sleep(2)

            correction(pepper, p_goal, pepper_positions=pepper_positions, path_positions=path_positions, errors=errors)

            print("Position after correction:", pepper.getPosition())
            print(f"Goal reached: {p_goal}")

            if errors:
                print("Movement task plot")
                path_x, path_y = zip(*path_positions)
                pepper_x, pepper_y = zip(*pepper_positions)

                useful_functions.motion_plot(path_x, path_y, pepper_x, pepper_y, errors)

        else:
            print("Ended of movement, because Robot detected obstacoles")

    else:
        print("Path not found")
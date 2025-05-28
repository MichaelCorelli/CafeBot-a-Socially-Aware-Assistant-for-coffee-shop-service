import pybullet as p
import matplotlib.pyplot as plt

def getGroundPlane_id():
    for object_id in range(p.getNumBodies()):
        object_info = p.getBodyInfo(object_id)
        objects = object_info[1].decode('utf-8') if object_info else ""
        if "ground_plane" in objects.lower():
            return object_id
    return None

def print_grid_created(grid, p_start_r, p_goal_r):

    for y in reversed(range(len(grid[0]))):

        j = ""
        for x in range(len(grid)):
            
            if p_start_r and (x, y) == p_start_r:
                j += "S"
            elif p_goal_r and (x, y) == p_goal_r:
                j += "G"
            elif grid[x][y] == 1:
                j += "1"
            else:
                j += "0"
        print(j)

def round_cell_size(val, cell_size=0.25):
    return round(val / cell_size) * cell_size

def motion_plot(x_path, y_path, x_robot, y_robot, errors):

    plt.figure(figsize=(10, 5))

    plt.subplot(1, 2, 1)
    plt.plot(x_path, y_path, label='Planned trajectory', linestyle='--', marker='o', color='r')
    plt.plot(x_robot, y_robot, label='Robot trajectory', linestyle='-', marker='o', color='k')
    plt.title("Planned and Robot Trajectory")
    plt.xlabel("X (m)")
    plt.ylabel("Y (m)")
    plt.legend()
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(errors, marker='o', linestyle='-', color='b')
    plt.title("Position Error")
    plt.xlabel("Step")
    plt.ylabel("Error (m)")
    plt.grid(True)

    plt.tight_layout()
    plt.show()
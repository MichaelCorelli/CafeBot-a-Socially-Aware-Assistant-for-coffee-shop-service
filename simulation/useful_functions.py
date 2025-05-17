import pybullet as p

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

def round_cell_size(val):

    if (val - int(val)) < 0.25:
        return int(val)
    elif (val - int(val)) < 0.75:
        return int(val) + 0.5
    else:
        return int(val) + 1

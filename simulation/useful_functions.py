import pybullet as p

def getGroundPlane_id():
    for object_id in range(p.getNumBodies()):
        object_info = p.getBodyInfo(object_id)
        objects = object_info[1].decode('utf-8') if object_info else ""
        if "ground_plane" in objects.lower():
            return object_id
    return None
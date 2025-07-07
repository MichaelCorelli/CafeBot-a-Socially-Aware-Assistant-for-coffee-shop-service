import pybullet as p
import time
from perception import PerceptionModule
from dynamic_planner import DynamicNavigator

"""
Simulation‐side navigation module with continuous replanning
using the dynamic semantic map from PerceptionModule.
"""

_perceptor = PerceptionModule()
_navigator = DynamicNavigator()

def get_robot_position(pepper):

    pos, _ = p.getBasePositionAndOrientation(pepper.robot_model)
    return pos[0], pos[1]

def teleport_to(pepper, x, y):
 
    pos, orn = p.getBasePositionAndOrientation(pepper.robot_model)
    z = pos[2]
    p.resetBasePositionAndOrientation(
        pepper.robot_model,
        [x, y, z],
        orn
    )
    time.sleep(0.05)

def moveToGoalDynamic(pepper, goal_xy):
  
    _perceptor.update_semantic_map(pepper)
    start_xy = get_robot_position(pepper)
    _navigator.navigate(
        start_xy      = start_xy,
        goal_xy       = goal_xy,
        move_callback = lambda x, y: teleport_to(pepper, x, y),
        check_callback= lambda: get_robot_position(pepper)
    )

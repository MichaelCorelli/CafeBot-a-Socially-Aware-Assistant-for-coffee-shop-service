from qibullet import SimulationManager
import time
import pybullet as p
import math
import numpy as np

import default_configuration_simulation
import useful_functions
import motion_simulation
import say_simulation

if __name__ == "__main__":
    simulation_manager = SimulationManager()

    client_id = simulation_manager.launchSimulation(gui=True)
    pepper = simulation_manager.spawnPepper(client_id, translation=[0, 0, 0], quaternion=[0, 0, 0, 1], spawn_ground_plane=True)

    print("Pepper spawned")

    #walls
    p.loadURDF("simulation/objects/wall.urdf", basePosition=[0, 8, 0], useFixedBase=True)
    p.loadURDF("simulation/objects/wall.urdf", basePosition=[0, -8, 0], useFixedBase=True)
    p.loadURDF("simulation/objects/wall.urdf", basePosition=[-8, 0, 0], baseOrientation=p.getQuaternionFromEuler([0, 0, math.pi / 2]), useFixedBase=True)
    wall_with_door_id = p.loadURDF("simulation/objects/wall_with_door.urdf", basePosition=[8, 0, 0], baseOrientation=p.getQuaternionFromEuler([0, 0, math.pi / 2]), useFixedBase=True)

    #door
    door_id = p.loadURDF("simulation/objects/door.urdf", [8, -0.5, 0])
    p.setJointMotorControl2(bodyUniqueId=door_id, jointIndex=0, controlMode=p.POSITION_CONTROL, targetPosition=0, force=10)

    #counter
    p.loadURDF("simulation/objects/counter.urdf", [-6, 0, 0])

    #furniture
    p.loadURDF("simulation/objects/furniture.urdf", [-7.5, -4, 0])
    p.loadURDF("simulation/objects/furniture.urdf", [-7.5, 4, 0])
    p.loadURDF("simulation/objects/furniture.urdf", [7.5, -4, 0])
    p.loadURDF("simulation/objects/furniture.urdf", [7.5, 4, 0])
    p.loadURDF("simulation/objects/furniture.urdf", basePosition=[-4, -7.5, 0], baseOrientation=p.getQuaternionFromEuler([0, 0, math.pi / 2]), useFixedBase=True)
    p.loadURDF("simulation/objects/furniture.urdf", basePosition=[-4, 7.5, 0], baseOrientation=p.getQuaternionFromEuler([0, 0, math.pi / 2]), useFixedBase=True)
    p.loadURDF("simulation/objects/furniture.urdf", basePosition=[4, -7.5, 0], baseOrientation=p.getQuaternionFromEuler([0, 0, math.pi / 2]), useFixedBase=True)
    p.loadURDF("simulation/objects/furniture.urdf", basePosition=[4, 7.5, 0], baseOrientation=p.getQuaternionFromEuler([0, 0, math.pi / 2]), useFixedBase=True)

    #table
    p.loadURDF("simulation/objects/table.urdf", [-3.5, -3.5, 0])
    p.loadURDF("simulation/objects/table.urdf", [3.5, -3.5, 0])
    p.loadURDF("simulation/objects/table.urdf", [3.5, 3.5, 0])
    p.loadURDF("simulation/objects/table.urdf", [-3.5, 3.5, 0])

    #chair
    p.loadURDF("simulation/objects/chair.urdf", [-3.5, -2.75, 0])
    p.loadURDF("simulation/objects/chair.urdf", [-3.5, -4.25, 0])
    p.loadURDF("simulation/objects/chair.urdf", [-2.75, -3.5, 0])
    p.loadURDF("simulation/objects/chair.urdf", [-4.25, -3.5, 0])

    p.loadURDF("simulation/objects/chair.urdf", [3.5, -2.75, 0])
    p.loadURDF("simulation/objects/chair.urdf", [3.5, -4.25, 0])
    p.loadURDF("simulation/objects/chair.urdf", [2.75, -3.5, 0])
    p.loadURDF("simulation/objects/chair.urdf", [4.25, -3.5, 0])

    p.loadURDF("simulation/objects/chair.urdf", [3.5, 2.75, 0])
    p.loadURDF("simulation/objects/chair.urdf", [3.5, 4.25, 0])
    p.loadURDF("simulation/objects/chair.urdf", [2.75, 3.5, 0])
    p.loadURDF("simulation/objects/chair.urdf", [4.25, 3.5, 0])

    p.loadURDF("simulation/objects/chair.urdf", [-3.5, 2.75, 0])
    p.loadURDF("simulation/objects/chair.urdf", [-3.5, 4.25, 0])
    p.loadURDF("simulation/objects/chair.urdf", [-2.75, 3.5, 0])
    p.loadURDF("simulation/objects/chair.urdf", [-4.25, 3.5, 0])

    #test
    test_id = p.createMultiBody(baseMass=60, baseCollisionShapeIndex=p.createCollisionShape(shapeType=p.GEOM_CYLINDER, radius=0.25, height=1.65), baseVisualShapeIndex=p.createVisualShape(shapeType=p.GEOM_CYLINDER, radius=0.25, length=1.65, rgbaColor=[1, 0, 0, 1]), basePosition=[3, 0, 0.825])

    print("World created")

    time.sleep(2)

    #Start simualtion

    #Wake up
    default_configuration_simulation.wake_up(pepper)

    #Welcome
    strsay = "Hello, welcome to CaféBot. I'm a Socially-Aware Assistant for coffee-shop service"
    default_configuration_simulation.welcome(pepper, strsay)

    #Say
    strsay = "How can I help you?"
    say_simulation.say(pepper, strsay)

    #Move to goal with A* algorithm
    p_goal = (1, 1)
    motion_simulation.moveToGoal(pepper, p_goal, ignored_ids=[test_id])

    p_goal = (-2.5, -1.75) #there is an obstacle here
    motion_simulation.moveToGoal(pepper, p_goal, ignored_ids=[test_id])

    #Rest
    default_configuration_simulation.reset_to_rest(pepper)

    #Ended simulation

    print("Quit")
    simulation_manager.stopSimulation(client_id)
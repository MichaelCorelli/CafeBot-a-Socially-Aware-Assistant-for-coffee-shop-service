from qibullet import SimulationManager
import time
import pybullet as p
import math
import numpy as np

from simulation import default_configuration_simulation
from simulation import useful_functions
from simulation import motion_simulation
from simulation import say_simulation
from simulation import dance_simulation

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

    #water bottle
    p.loadURDF("simulation/objects/water_bottle.urdf", [-3.45, -3.55, 0.66])
    p.loadURDF("simulation/objects/water_bottle.urdf", [3.45, -3.55, 0.66])
    p.loadURDF("simulation/objects/water_bottle.urdf", [3.45, 3.55, 0.66])
    p.loadURDF("simulation/objects/water_bottle.urdf", [-3.45, 3.55, 0.66])

    #orange juice
    p.loadURDF("simulation/objects/orange_juice.urdf", [-3.55, -3.45, 0.66])
    p.loadURDF("simulation/objects/orange_juice.urdf", [3.55, -3.45, 0.66])
    p.loadURDF("simulation/objects/orange_juice.urdf", [3.55, 3.45, 0.66])
    p.loadURDF("simulation/objects/orange_juice.urdf", [-3.55, 3.45, 0.66])

    #cappuccino
    p.loadURDF("simulation/objects/cappuccino.urdf", [-3.2, -3.45, 0.66])
    p.loadURDF("simulation/objects/cappuccino.urdf", [3.2, -3.45, 0.66])
    p.loadURDF("simulation/objects/cappuccino.urdf", [3.2, 3.45, 0.66])
    p.loadURDF("simulation/objects/cappuccino.urdf", [-3.2, 3.45, 0.66])

    #espresso
    p.loadURDF("simulation/objects/espresso.urdf", [-3.45, -3.2, 0.66])
    p.loadURDF("simulation/objects/espresso.urdf", [3.45, -3.2, 0.66])
    p.loadURDF("simulation/objects/espresso.urdf", [3.45, 3.2, 0.66])
    p.loadURDF("simulation/objects/espresso.urdf", [-3.45, 3.2, 0.66])

    #cornetto
    p.loadURDF("simulation/objects/cornetto.urdf", [-3.25, -3.25, 0.66])
    p.loadURDF("simulation/objects/cornetto.urdf", [3.25, -3.25, 0.66])
    p.loadURDF("simulation/objects/cornetto.urdf", [3.25, 3.25, 0.66])
    p.loadURDF("simulation/objects/cornetto.urdf", [-3.25, 3.25, 0.66])

    #tea
    p.loadURDF("simulation/objects/tea.urdf", [-3.8, -3.5, 0.66])
    p.loadURDF("simulation/objects/tea.urdf", [3.8, -3.5, 0.66])
    p.loadURDF("simulation/objects/tea.urdf", [3.8, 3.5, 0.66])
    p.loadURDF("simulation/objects/tea.urdf", [-3.8, 3.5, 0.66])

    #muffin
    p.loadURDF("simulation/objects/muffin.urdf", [-3.5, -3.8, 0.66])
    p.loadURDF("simulation/objects/muffin.urdf", [3.5, -3.8, 0.66])
    p.loadURDF("simulation/objects/muffin.urdf", [3.5, 3.8, 0.66])
    p.loadURDF("simulation/objects/muffin.urdf", [-3.5, 3.8, 0.66])

    #sandwich
    p.loadURDF("simulation/objects/sandwich.urdf", [-3.75, -3.75, 0.66])
    p.loadURDF("simulation/objects/sandwich.urdf", [3.75, -3.75, 0.66])
    p.loadURDF("simulation/objects/sandwich.urdf", [3.75, 3.75, 0.66])
    p.loadURDF("simulation/objects/sandwich.urdf", [-3.75, 3.75, 0.66])

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
    p_goal = (5, 5)
    motion_simulation.moveToGoal(pepper, p_goal, ignored_ids=[test_id])

    p_goal = (5, -5)
    motion_simulation.moveToGoal(pepper, p_goal, ignored_ids=[test_id])

    p_goal = (-5, -5)
    motion_simulation.moveToGoal(pepper, p_goal, ignored_ids=[test_id])

    p_goal = (-5, 5)
    motion_simulation.moveToGoal(pepper, p_goal, ignored_ids=[test_id])

    p_goal = (0, 0)
    motion_simulation.moveToGoal(pepper, p_goal, ignored_ids=[test_id])

    p_goal = (3, 0) #the test is here
    motion_simulation.moveToGoal(pepper, p_goal, ignored_ids=[test_id])

    #Dance
    strsay = "I'm dancing"
    dance_simulation.dance(pepper, strsay)

    #Rest
    default_configuration_simulation.reset_to_rest(pepper)

    #Ended simulation

    print("Quit")
    simulation_manager.stopSimulation(client_id)
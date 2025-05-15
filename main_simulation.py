from qibullet import SimulationManager
import time
import pybullet as p
import math

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

    #tables
    p.loadURDF("simulation/objects/table.urdf", [-2.5, -2.5, 0])
    p.loadURDF("simulation/objects/table.urdf", [2.5, -2.5, 0])
    p.loadURDF("simulation/objects/table.urdf", [2.5, 2.5, 0])
    p.loadURDF("simulation/objects/table.urdf", [-2.5, 2.5, 0])

    #chairs
    p.loadURDF("simulation/objects/chair.urdf", [-2.5, -1.75, 0], p.getQuaternionFromEuler([0, 0, 0]))
    p.loadURDF("simulation/objects/chair.urdf", [-2.5, -3.25, 0], p.getQuaternionFromEuler([0, 0, 0]))
    p.loadURDF("simulation/objects/chair.urdf", [-1.75, -2.5, 0], p.getQuaternionFromEuler([0, 0, 0]))
    p.loadURDF("simulation/objects/chair.urdf", [-3.25, -2.5, 0], p.getQuaternionFromEuler([0, 0, 0]))

    p.loadURDF("simulation/objects/chair.urdf", [2.5, -1.75, 0], p.getQuaternionFromEuler([0, 0, 0]))
    p.loadURDF("simulation/objects/chair.urdf", [2.5, -3.25, 0], p.getQuaternionFromEuler([0, 0, 0]))
    p.loadURDF("simulation/objects/chair.urdf", [1.75, -2.5, 0], p.getQuaternionFromEuler([0, 0, 0]))
    p.loadURDF("simulation/objects/chair.urdf", [3.25, -2.5, 0], p.getQuaternionFromEuler([0, 0, 0]))

    p.loadURDF("simulation/objects/chair.urdf", [2.5, 1.75, 0], p.getQuaternionFromEuler([0, 0, 0]))
    p.loadURDF("simulation/objects/chair.urdf", [2.5, 3.25, 0], p.getQuaternionFromEuler([0, 0, 0]))
    p.loadURDF("simulation/objects/chair.urdf", [1.75, 2.5, 0], p.getQuaternionFromEuler([0, 0, 0]))
    p.loadURDF("simulation/objects/chair.urdf", [3.25, 2.5, 0], p.getQuaternionFromEuler([0, 0, 0]))

    p.loadURDF("simulation/objects/chair.urdf", [-2.5, 1.75, 0], p.getQuaternionFromEuler([0, 0, 0]))
    p.loadURDF("simulation/objects/chair.urdf", [-2.5, 3.25, 0], p.getQuaternionFromEuler([0, 0, 0]))
    p.loadURDF("simulation/objects/chair.urdf", [-1.75, 2.5, 0], p.getQuaternionFromEuler([0, 0, 0]))
    p.loadURDF("simulation/objects/chair.urdf", [-3.25, 2.5, 0], p.getQuaternionFromEuler([0, 0, 0]))

    print("World created")

    time.sleep(2)

    #Start simualtion
    #Wake up
    default_configuration_simulation.wake_up(pepper)

    #Welcome
    #strsay = "Hello, welcome to CaféBot. I'm a Socially-Aware Assistant for coffee-shop service"
    #default_configuration_simulation.welcome(pepper, strsay)

    #Say
    #strsay = "How can I help you?"
    #say_simulation.say(pepper, strsay)

    #Move to goal with A* algorithm
    ground_plane_id = useful_functions.getGroundPlane_id()
    pepper_id = pepper.robot_model
    grid_size = (16, 16)

    grid = motion_simulation.obstacles_grid(ground_plane_id, pepper_id, grid_size)
    p = pepper.getPosition()

    p_start = (p[0], p[1])
    p_goal = (4.25, 4.25)

    p_start_r = (round(p_start[0]), round(p_start[1]))
    p_goal_r = (round(p_goal[0]), round(p_goal[1]))
    print(f"Start position: {p_start_r} and goal position: {p_goal_r}")

    path = motion_simulation.A_star_algorithm(p_start_r, p_goal_r, grid)

    if path:
        print(f"Path found: {path}")
        motion_simulation.moveToGoal(pepper, path)

        print(f"Goal reached: {p_goal_r}")
        time.sleep(1)
    else:
        print("Path not found")

    p = pepper.getPosition()

    p_start = (p[0], p[1])
    p_goal = (-7, -7)

    p_start_r = (round(p_start[0]), round(p_start[1]))
    p_goal_r = (round(p_goal[0]), round(p_goal[1]))
    print(f"Start position: {p_start_r} and goal position: {p_goal_r}")

    path = motion_simulation.A_star_algorithm(p_start_r, p_goal_r, grid)

    if path:
        print(f"Path found: {path}")
        motion_simulation.moveToGoal(pepper, path)

        print(f"Goal reached: {p_goal_r}")
        time.sleep(1)
    else:
        print("Path not found")

    #Rest
    default_configuration_simulation.reset_to_rest(pepper)

    print("Quit")
    simulation_manager.stopSimulation(client_id)


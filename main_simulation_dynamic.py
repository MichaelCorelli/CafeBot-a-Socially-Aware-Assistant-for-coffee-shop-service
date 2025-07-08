from qibullet import SimulationManager, PepperVirtual
import time
import pybullet as p
import math
import numpy as np
import json
from simulation import default_configuration_simulation, motion_simulation, say_simulation, dance_simulation, perception, simulation_llm_bridge, live_speech

dynamic_semantic_map = []
WAKE_WORD = "pepper"

def build_environment(client_id):
    print("Building environment...")
    
    p.loadURDF("simulation/objects/wall.urdf", basePosition=[0, 8, 0], useFixedBase=True)
    p.loadURDF("simulation/objects/wall.urdf", basePosition=[0, -8, 0], useFixedBase=True)
    p.loadURDF("simulation/objects/wall.urdf", basePosition=[-8, 0, 0], baseOrientation=p.getQuaternionFromEuler([0, 0, math.pi / 2]), useFixedBase=True)
    wall_with_door_id = p.loadURDF("simulation/objects/wall_with_door.urdf", basePosition=[8, 0, 0], baseOrientation=p.getQuaternionFromEuler([0, 0, math.pi / 2]), useFixedBase=True)

    door_id = p.loadURDF("simulation/objects/door.urdf", [8, -0.5, 0])
    p.setJointMotorControl2(bodyUniqueId=door_id, jointIndex=0, controlMode=p.POSITION_CONTROL, targetPosition=0, force=10)

    p.loadURDF("simulation/objects/counter.urdf", [-6, 0, 0], physicsClientId=client_id)
    p.loadURDF("simulation/objects/table.urdf", [-3.5, -3.5, 0], physicsClientId=client_id)
    p.loadURDF("simulation/objects/cappuccino.urdf", [-3.45, -3.55, 0.66], physicsClientId=client_id)
  
    person_id = p.createMultiBody(baseMass=60, baseCollisionShapeIndex=p.createCollisionShape(shapeType=p.GEOM_CYLINDER, radius=0.25, height=1.65), basePosition=[2, -2, 0.825], physicsClientId=client_id)
    print("Environment built.")
    return [person_id]

def _make_view_proj(pepper, camera_link):

    link_state = p.getLinkState(pepper.robot_model, camera_link,
                                computeForwardKinematics=True)
    cam_pos   = link_state[4]     
    cam_orn   = link_state[5]         
    cam_mat   = p.getMatrixFromQuaternion(cam_orn)
    cam_dir   = [cam_mat[0], cam_mat[3], cam_mat[6]] 
    cam_up    = [cam_mat[2], cam_mat[5], cam_mat[8]] 
 
    target    = [cam_pos[i] + cam_dir[i] for i in range(3)]
    view      = p.computeViewMatrix(cam_pos, target, cam_up)
    proj      = p.computeProjectionMatrixFOV(fov=60,
                                             aspect=4/3,
                                             nearVal=0.1,
                                             farVal=5.0)
    return view, proj

def getCameraViewMatrix(self, cam_id=2):
   
    link_index = {0: 59, 1: 59, 2: 60}.get(cam_id, 60)  
    return _make_view_proj(self, link_index)[0]

def getCameraProjectionMatrix(self, cam_id=2):
    link_index = {0: 59, 1: 59, 2: 60}.get(cam_id, 60)
    return _make_view_proj(self, link_index)[1]

PepperVirtual.getCameraViewMatrix = getCameraViewMatrix
PepperVirtual.getCameraProjectionMatrix = getCameraProjectionMatrix

def scan_environment(pepper, perception_module):
    print("Starting environment scan…")
    all_found_objects = []
    initial_pose, initial_orient = p.getBasePositionAndOrientation(pepper.robot_model)

    for angle in np.linspace(0, 2*np.pi, 10, endpoint=False):
        p.resetBasePositionAndOrientation(
            pepper.robot_model,
            initial_pose,
            p.getQuaternionFromEuler([0, 0, angle])
        )
        time.sleep(0.1)
        img, depth_buf, view, proj = perception_module.get_camera_image(pepper)
        if img is None:
            continue

        det2d = perception_module.detect_objects(img)
        det3d = perception_module.localize_objects_3d(det2d, depth_buf, view, proj)
        all_found_objects.extend(det3d)

    p.resetBasePositionAndOrientation(
        pepper.robot_model,
        initial_pose,
        p.getQuaternionFromEuler([0, 0, 0])
    )

    unique = {
      f"{o['label']}_{tuple(np.round(o['world_coordinates'],0))}": o
      for o in all_found_objects
    }
    global dynamic_semantic_map
    dynamic_semantic_map = list(unique.values())
    print(f"Scan complete. Found {len(dynamic_semantic_map)} unique objects.")


def run_interaction(command, pepper, menu_data, ignored_obstacles):
    """Helper function to process a command and handle the response."""
    if not command: return
    llm_response = simulation_llm_bridge.process_user_command(command)
    simulation_llm_bridge.handle_llm_response(pepper, llm_response, dynamic_semantic_map, menu_data, ignored_obstacles)

if __name__ == "__main__":
    try:
        with open("menu.json", "r", encoding="utf-8") as f:
            menu_data = json.load(f) #
    except FileNotFoundError:
        menu_data = []

    simulation_manager = SimulationManager()
    client_id = simulation_manager.launchSimulation(gui=True)
    pepper = simulation_manager.spawnPepper(client_id, translation=[0, 0, 0], quaternion=[0, 0, 0, 1], spawn_ground_plane=True)
    
    ignored_obstacles = build_environment(client_id)
    perception_module = perception.PerceptionModule()
    
 
    
    default_configuration_simulation.wake_up(pepper) #
    say_simulation.say(pepper, "Hello, I am CaféBot. I am scanning the environment.") #
    scan_environment(pepper, perception_module)
    motion_simulation.moveToGoal(pepper, (0.0, 0.0), ignored_obstacles) #


    
    print("\n\n--- DEMO SCENARIO 1: CUSTOMER INTERACTION ---")
    say_simulation.say(pepper, "I've finished scanning. I will now run a short demo to show my capabilities.") 
    time.sleep(2)
    
    print("\n[SCENARIO] Simulating a customer's first question...")
    run_interaction("Hello, what is the price of a cappuccino?", pepper, menu_data, ignored_obstacles)
    time.sleep(2)
    

    print("\n[SCENARIO] Simulating the customer's follow-up command...")
    run_interaction("Great, can you take me to the cappuccino?", pepper, menu_data, ignored_obstacles)
    time.sleep(2)
    
    print("\n\n--- DEMO SCENARIO 2: WORKER INTERACTION ---")
    simulation_llm_bridge.reset_session()
    say_simulation.say(pepper, "A new user has arrived. I have reset my context.") #
    time.sleep(2)
    
    print("\n[SCENARIO] Simulating a worker's question...")
    run_interaction("Cappuccino allergen check.", pepper, menu_data, ignored_obstacles)
    time.sleep(2)
    

    
    print("\n\n--- FREE INTERACTION MODE ---")
    say_simulation.say(pepper, f"Demo complete. Now, say my name, '{WAKE_WORD}', to give me a command with your voice.") 
    
    while True:
        try:
            text = live_speech.listen_for_input(f"Waiting for wake word '{WAKE_WORD}'...")
            
            if text and WAKE_WORD in text:
                say_simulation.say(pepper, "Yes? How can I help?") 
                command = live_speech.listen_for_input("Listening for your command...")
                
                if command:
                    run_interaction(command, pepper, menu_data, ignored_obstacles)
                    say_simulation.say(pepper, f"Is there anything else? Just say '{WAKE_WORD}' again if you need me.") 
                else:
                    say_simulation.say(pepper, "I was listening, but I didn't get that. Please try again.")

        except (KeyboardInterrupt):
            print("\nExiting voice loop.")
            break

    
    say_simulation.say(pepper, "Goodbye and have a great day!") #
    dance_simulation.dance(pepper, "See you soon!") #
    default_configuration_simulation.reset_to_rest(pepper) #
    
    print("Simulation finished. Stopping...")
    time.sleep(2)
    simulation_manager.stopSimulation(client_id)
import time

import say_simulation

def wake_up(pepper):

    time.sleep(2)
    print("Wakes up: start")

    name = ["HeadPitch"]
    angle = [-0.2]
    pepper.setAngles(name, angle, 0.2)

    names = ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LHand", "RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RHand"]
    angles = [1.5, 0.2, -1.3, -0.5, 0, 1.5, -0.2, 1.3, 0.5, 0]
    pepper.setAngles(names, angles, 0.2)

    print("Wakes up: ended")
    time.sleep(2)

def welcome(pepper, strsay):

    time.sleep(2)
    print("Welcome: start")

    #Init
    joint_names = ["HeadYaw", "HeadPitch", "LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw", "LHand", "RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "RHand"]
    joint_angles = [0, 0, 1.5, 0.3, -1.2, -0.5, 0, 0, 1.5, -0.3, 1.2, 0.5, 0, 0]
    pepper.setAngles(joint_names, joint_angles, 0.2)

    time.sleep(2)

    #Welcome movement
    names = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RHand", "HeadYaw", "HeadPitch"]
    angles = [0.1, -0.4, 1.3, 1.5, 1, 0.1, -0.15]
    times = [1]*len(names)
    isAbsolute = True
    pepper.setAngles(names, angles, 0.3)

    #Welcome say
    say_simulation.say(pepper, strsay)

    #Welcome movement
    names = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "HeadYaw", "HeadPitch"]
    angles_1 = [0.1, -0.4, 1.3, 0.5, 0.1, -0.15]
    angles_2 = [0.1, -0.4, 1.3, 1.5, 0.1, -0.15]
    times = [1] * len(names)
    
    for _ in range(3):
        pepper.setAngles(names, angles_1, 0.3)
        time.sleep(0.5)
        pepper.setAngles(names, angles_2, 0.3)
        time.sleep(0.5)

    time.sleep(3)

    #Init
    names = ["HeadYaw", "HeadPitch", "LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw", "LHand", "RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "RHand"]
    angles = [0, 0, 1.5, 0.3, -1.2, -0.5, 0, 0, 1.5, -0.3, 1.2, 0.5, 0, 0]
    pepper.setAngles(names, angles, 0.2)

    print("Welcome: ended")
    time.sleep(2)

def reset_to_rest(pepper):

    time.sleep(2)
    print("Reset to rest position: start")
    names = ["HeadYaw", "HeadPitch", "LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw", "LHand", "RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "RHand"]
    angles = [0, 0.3, 1.6, 0.1, -1.4, -0.2, 0, 0, 1.6, -0.1, 1.4, 0.2, 0, 0]
    pepper.setAngles(names, angles, 0.15)
    print("Reset to rest position: ended")
    time.sleep(2)
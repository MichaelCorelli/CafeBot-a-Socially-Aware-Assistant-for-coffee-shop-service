import time

import say_simulation

def dance(pepper, strsay):

    time.sleep(2)
    print("Dance: start")

    #Init
    joint_names = ["HeadYaw", "HeadPitch", "LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw", "LHand", "RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "RHand"]
    joint_angles = [0, 0, 1.5, 0.3, -1.2, -0.5, 0, 0, 1.5, -0.3, 1.2, 0.5, 0, 0]
    pepper.setAngles(joint_names, joint_angles, 0.2)

    time.sleep(2)

    #Dance say
    say_simulation.say(pepper, strsay)

    #Dance movement
    names = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "HeadYaw", "HeadPitch"]
    angles_1 = [0.1, 0.4, 1.3, 0.5, 0.1,  0.4, -1.3, -0.5, 0.3, -0.15]
    angles_2 = [-0.1, -0.4, 1.3, 1.5, 0.1,  0.4, -1.3, -1.5, -0.3, -0.15]
    times = [1] * len(names)
    
    for _ in range(5):
        pepper.setAngles(names, angles_1, 0.3)
        time.sleep(0.5)
        pepper.setAngles(names, angles_2, 0.3)
        time.sleep(0.5)

    time.sleep(3)

    #Init
    names = ["HeadYaw", "HeadPitch", "LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw", "LHand", "RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "RHand"]
    angles = [0, 0, 1.5, 0.3, -1.2, -0.5, 0, 0, 1.5, -0.3, 1.2, 0.5, 0, 0]
    pepper.setAngles(names, angles, 0.2)

    print("Dance: ended")
    time.sleep(2)

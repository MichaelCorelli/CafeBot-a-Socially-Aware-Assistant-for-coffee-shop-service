import time

import say

def wake_up(motion_service):

    time.sleep(2)
    print("Wakes up: start")
    motion_service.wakeUp()
    print("Wakes up: ended")
    time.sleep(2)

def welcome(posture_service, motion_service, ans_service, strsay):

    time.sleep(2)
    print("Welcome: start")

    #Init 
    posture_service.goToPosture("StandInit", 0.5)

    time.sleep(2)

    #Welcome movement
    names = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RHand", "HeadYaw", "HeadPitch"]
    angles = [0.1, -0.4, 1.3, 1.5, 1, 0.1, -0.15]
    times = [1]*len(names)
    isAbsolute = True
    motion_service.angleInterpolation(names, angles, times, isAbsolute)

    #Welcome say
    say.say(ans_service, strsay)

    #Welcome movement
    names = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll"]
    angles_1 = [0.1, -0.4, 1.3, 0.5]
    angles_2 = [0.1, -0.4, 1.3, 1.5]
    times = [1] * len(names)
    isAbsolute = True
    
    for _ in range(3):
        motion_service.angleInterpolation(names, angles_1, times, isAbsolute)
        time.sleep(0.5)
        motion_service.angleInterpolation(names, angles_2, times, isAbsolute)
        time.sleep(0.5)

    time.sleep(3)

    #Init
    posture_service.goToPosture("StandInit", 0.5)

    print("Welcome: ended")
    time.sleep(2)

def reset_to_rest(motion_service):

    time.sleep(2)
    print("Reset to rest position: start")
    motion_service.rest()
    print("Reset to rest position: ended")
    time.sleep(2)
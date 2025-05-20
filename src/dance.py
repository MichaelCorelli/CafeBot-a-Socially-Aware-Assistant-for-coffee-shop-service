import time

import say

def dance(posture_service, motion_service, ans_service, strsay):

    time.sleep(2)
    print("Dance: start")

    #Init 
    posture_service.goToPosture("StandInit", 0.5)

    time.sleep(2)

    #Dance say
    say.say(ans_service, strsay)

    #Dance movement
    names = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "HeadYaw", "HeadPitch"]
    angles_1 = [0.1, 0.4, 1.3, 0.5, 0.1,  0.4, -1.3, -0.5, 0.3, -0.15]
    angles_2 = [-0.1, -0.4, 1.3, 1.5, 0.1,  0.4, -1.3, -1.5, -0.3, -0.15]
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

    print("Dance: ended")
    time.sleep(2)

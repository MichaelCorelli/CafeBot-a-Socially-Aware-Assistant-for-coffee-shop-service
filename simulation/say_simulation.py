import pybullet as p
import time
from threading import Thread

def say(pepper, strsay):
    
    time.sleep(1)

    print("Say: start")

    time_d = max(2, len(strsay)*0.1)

    def speack():
        position = pepper.getPosition()
        speack_position = [position[0], position[1], position[2] + 2]
        p.addUserDebugText(strsay, speack_position, textColorRGB=[0, 0, 0], textSize=1.5, lifeTime=time_d)

    def move():

        time_tot = time.time() + time_d

        while time.time() < time_tot:
            pepper.setAngles(["HeadYaw", "HeadPitch"], [0.1, -0.2], 0.1)
            time.sleep(0.5)
            pepper.setAngles(["HeadYaw", "HeadPitch"], [-0.1, 0.2], 0.1)
            time.sleep(0.5)

    speack_thread = Thread(target=speack)
    move_thread = Thread(target=move)

    speack_thread.start()
    move_thread.start()

    speack_thread.join()
    move_thread.join()

    print(strsay)
    print("Say: ended")

    time.sleep(1)
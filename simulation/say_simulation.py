import pybullet as p
import time
from threading import Thread

def say(pepper, strsay):

    time.sleep(2)

    def speack():
        position = pepper.getPosition()
        speack_position = [position[0], position[1], position[2] + 2]
        text_id = p.addUserDebugText(strsay, speack_position, textColorRGB=[0, 0, 0], textSize=1.5, lifeTime=3)

    def move():
        for _ in range(3):
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

    time.sleep(2)
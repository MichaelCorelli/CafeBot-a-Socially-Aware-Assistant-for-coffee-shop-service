# -*- coding: utf-8 -*-

import sys
import os
import default_configuration
import motion
import say
import qi
import argparse
import time
import math

def getenv(envstr, default = None):
    if envstr in os.environ:
        return os.environ[envstr]
    else:
        return default

def main():
    global motion_service
    parser = argparse.ArgumentParser()
    parser.add_argument("--pip", type=str, default=getenv('PEPPER_IP'),
                        help="Robot IP address.")
    parser.add_argument("--pport", type=int, default=getenv('PEPPER_PORT'),
                        help="Naoqi port number")
    parser.add_argument("--sentence", type=str, default="Hello, welcome to CaféBot. I'm a Socially-Aware Assistant for coffee-shop service",
                        help="Sentence to say")

    args = parser.parse_args()
    pip = args.pip
    pport = args.pport
    strsay = args.sentence

    try:
        connection_url = "tcp://" + pip + ":" + str(pport)
        app = qi.Application(["Say", "--qi-url=" + connection_url ])
    except RuntimeError:
        print ("Can't connect to Naoqi at ip \"" + pip + "\" on port " + str(pport) +".\n"
               "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)

    app.start()
    session = app.session

    posture_service = session.service("ALRobotPosture")
    motion_service = session.service("ALMotion")
    ans_service = session.service("ALAnimatedSpeech")

    default_configuration.wake_up(motion_service)

    default_configuration.welcome(posture_service, motion_service, ans_service, strsay)
    
    default_configuration.reset_to_rest(motion_service)

if __name__ == "__main__":
    main()
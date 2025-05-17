import time

def say(ans_service, strsay):

    time.sleep(2)
    
    print("Say: start")
    ans_service.say(strsay, {"bodyLanguageMode": "contextual"})

    print(strsay)
    print("Say: ended")

    time.sleep(2)
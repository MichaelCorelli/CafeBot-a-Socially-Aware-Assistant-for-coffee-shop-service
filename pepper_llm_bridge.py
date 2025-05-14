import qi
import requests
import json
import threading
import time
import logging
from urllib.parse import quote


PEPPER_IP        = "192.168.1.101"
PEPPER_PORT      = 9559
LLM_SERVER_URL   = "http://edgepc:8000/chat"
DISPLAY_URL      = "http://edgepc:8000/display"
ASR_CONF         = 0.4 
WAKE_WORD        = "pepper"
LISTENING        = False

with open("menu.json", "r", encoding="utf-8") as f:
    menu_items = json.load(f)

logging.basicConfig(
    filename="pepper_llm_bridge.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)  

session = qi.Session()
session.connect(f"tcp://{PEPPER_IP}:{PEPPER_PORT}")

tts       = session.service("ALAnimatedSpeech")
motion    = session.service("ALMotion")
tablet    = session.service("ALTabletService")
memory    = session.service("ALMemory")
asr       = session.service("ALSpeechRecognition")


asr.setLanguage("Italian")
asr.setVocabulary([], True)  
asr.subscribe("CafeBotASR")

def cleanup():
    """Unsubscribe cleanly on exit."""
    try:
        asr.unsubscribe("CafeBotASR")
        memory.unsubscribeToEvent("WordRecognized", "pepper_llm_bridge")
    except Exception:
        pass

def handle_function_call(fn_call: dict):
    """Execute navigate_to, get_price or get_allergens locally."""
    name = fn_call["name"]
    args = json.loads(fn_call["arguments"])

    if name == "navigate_to":
        location = args["location"]
        logging.info(f"→ navigating to {location}")
        memory.raiseEvent("NavTarget", location)

    elif name == "get_price":
        product = args["product"].lower()
        item = next((i for i in menu_items if i["name"].lower()==product), None)
        reply = f"{item['name']} costs €{item['price']}." if item else f"Sorry, I don’t have the price for {product}."
        tts.say(reply)

    elif name == "get_allergens":
        product = args["product"].lower()
        item = next((i for i in menu_items if i["name"].lower()==product), None)
        if item:
            allergens = item.get("allergens", [])
            reply = f"Allergens for {item['name']}: {', '.join(allergens)}." if allergens else f"{item['name']} has no listed allergens."
        else:
            reply = f"Sorry, I don’t have allergen info for {product}."
        tts.say(reply)


def process_command(text: str):
    """Send text to LLM, handle function_call or normal reply, and log."""
    start = time.time()
    payload = {"text": text, "role": "customer"}

    try:
        resp = requests.post(LLM_SERVER_URL, json=payload, timeout=5.0)
        resp.raise_for_status()
        msg = resp.json()
    except Exception as e:
        logging.error(f"LLM request failed: {e}")
        tts.say("\\rspd=90\\Sorry, I’m having trouble connecting to the brain.")
        return

    if msg.get("function_call"):
        handle_function_call(msg["function_call"])
        logging.info(f"Function called: {msg['function_call']['name']}")
        return

    reply   = msg.get("content", "").strip()
    gesture = msg.get("gesture", "").strip()

    if reply:
        tts.say(reply)

    if gesture.lower() == "pointleft":
        motion.post.angleInterpolation("LShoulderPitch", -0.2, 1.0, True)
    elif gesture.lower() == "pointright":
        motion.post.angleInterpolation("RShoulderPitch", 0.2, 1.0, True)
    elif gesture.lower() == "nod":
        motion.post.angleInterpolation("HeadPitch", 0.3, 1.0, True)

    tablet.loadUrl(f"{DISPLAY_URL}?text={quote(reply)}")
    
    elapsed = time.time() - start
    logging.info(f"user='{text}' | reply='{reply}' | gesture='{gesture}' | dt={elapsed:.2f}s")

def on_word_recognized(key, value, _):
    """ASR callback: wake-word + non-blocking dispatch."""
    global LISTENING
    text, conf = value[0], value[1]

    if conf < ASR_CONF:
        return

    text_lower = text.lower()
    logging.info(f"ASR recognized '{text}' (conf={conf:.2f})")
    if LISTENING:
        if text_lower == "stop":
            LISTENING = False
            tts.say("Ok, I’m listening again.")
            return
        elif text_lower == "menu":
            tts.say("Here is the menu.")
            tablet.loadUrl(f"{DISPLAY_URL}?text={quote('Menu')}")
            return
        elif text_lower == "exit":
            tts.say("Goodbye!")
            cleanup()
            exit(0)
    if not LISTENING:
        if WAKE_WORD in text_lower:
            LISTENING = True
            tts.say("Yes?")
        return

    LISTENING = False
    threading.Thread(target=process_command, args=(text,)).start()

memory.subscribeToEvent("WordRecognized", "pepper_llm_bridge", "on_word_recognized")
print("Pepper LLM bridge running. Say ‘Pepper’ to wake me.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down...")
finally:
    cleanup()
    print("Cleanup done.")

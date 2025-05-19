import qi
import requests
import json
import threading
import time
import logging
from urllib.parse import quote


PEPPER_IP = os.getenv("PEPPER_IP", "127.0.0.1")
PEPPER_PORT = int(os.getenv("PEPPER_PORT", 9559))
LLM_SERVER_URL = os.getenv("LLM_SERVER_URL", "http://localhost:8000/chat")
DISPLAY_URL_BASE = os.getenv("DISPLAY_URL_BASE", "http://localhost:8000")
ASR_CONFIDENCE_THRESHOLD = float(os.getenv("ASR_CONFIDENCE_THRESHOLD", 0.45))
WAKE_WORD = os.getenv("WAKE_WORD", "pepper").lower()

CURRENT_USER_ROLE = "unknown"
SESSION_TIMEOUT_SECONDS = 300
LAST_INTERACTION_TIME = time.time()
CURRENT_LANGUAGE = "English"

try:
    with open("menu.json", "r", encoding="utf-8") as f:
        menu_items = json.load(f)
except FileNotFoundError:
    menu_items = []

logging.basicConfig(
    filename="pepper_llm_bridge.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s"
) 

session = None
try:
    session = qi.Session()
    session.connect(f"tcp://{PEPPER_IP}:{PEPPER_PORT}")
    logging.info(f"Successfully connected to Naoqi at {PEPPER_IP}:{PEPPER_PORT}")
    tts = session.service("ALAnimatedSpeech")
    motion = session.service("ALMotion")
    tablet = session.service("ALTabletService")
    memory = session.service("ALMemory")
    asr = session.service("ALSpeechRecognition")
    awareness = session.service("ALBasicAwareness")
    posture = session.service("ALRobotPosture")
    animation_player = session.service("ALAnimationPlayer")

    if session.service("ALAutonomousLife").getState() != "disabled":
        session.service("ALAutonomousLife").setState("disabled")
    posture.goToPosture("StandInit", 0.8)
    motion.wakeUp()
    
    asr.setLanguage(CURRENT_LANGUAGE)
    base_vocabulary = [WAKE_WORD, "stop", "menu", "esci", "termina", "arrivederci", "grazie"]
    asr.setVocabulary(list(set(base_vocabulary)), True)
    asr.subscribe("CafeBotASR_Combined")

    if awareness:
        awareness.setEnabled(True); awareness.setStimulusDetectionEnabled("Sound", True)
        awareness.setTrackingMode("Head"); awareness.setEngagementMode("SemiEngaged")
    logging.info("NAOqi services initialized and configured for combined prompt.")

except RuntimeError as e:
    logging.error(f"CRITICAL: Cannot connect to Naoqi. Error: {e}")
except Exception as e:
    logging.error(f"Error initializing Naoqi services: {e}")


LISTENING_ACTIVE = False

def reset_session_state():
    global CURRENT_USER_ROLE, LAST_INTERACTION_TIME
    logging.info(f"Resetting session state. Previous role: {CURRENT_USER_ROLE}")
    CURRENT_USER_ROLE = "unknown"
    LAST_INTERACTION_TIME = time.time()
    if tablet: display_on_tablet(text_to_display=f"CaféBot Ready\nRole: Waiting...\nSay '{WAKE_WORD}'")

def check_session_timeout():
    if CURRENT_USER_ROLE != "unknown":
        if (time.time() - LAST_INTERACTION_TIME) > SESSION_TIMEOUT_SECONDS:
            logging.info("Session timed out.")
            if tts: tts.say("It's been a while. Let's start fresh.")
            reset_session_state()
            return True
    return False

def cleanup():
    global LISTENING_ACTIVE
    LISTENING_ACTIVE = False; logging.info("Cleanup initiated.")
    if asr and session and session.isConnected(): asr.unsubscribe("CafeBotASR_Combined")
    if awareness and session and session.isConnected(): awareness.setEnabled(False)
    if tablet and session and session.isConnected(): tablet.hideWebview()
    if motion and posture and session and session.isConnected(): motion.rest()


def display_on_tablet(text_to_display=None, image_url=None, show_map=False, options=None):
    if not tablet or not session or not session.isConnected(): return
    base_tablet_url = f"{DISPLAY_URL_BASE}/tablet_view" 
    params = []
    if text_to_display: params.append(f"text={quote(text_to_display)}")
    if image_url: params.append(f"image={quote(image_url)}")
    if show_map: params.append(f"map=true")
    if options and isinstance(options, list):
        for i, opt in enumerate(options): params.append(f"option{i+1}={quote(opt)}")
    final_url = base_tablet_url + (("?" + "&".join(params)) if params else "")
    try: tablet.showWebview(final_url)
    except Exception as e: logging.error(f"Error displaying on tablet: {e}. URL: {final_url}")


def perform_gesture(gesture_name_or_animation: str):
    if not motion or not animation_player or not session or not session.isConnected(): return
    try:
        if "/" in gesture_name_or_animation or animation_player.getInstalledBehaviors().count(gesture_name_or_animation) > 0:
            animation_player.post.run(gesture_name_or_animation)
        elif gesture_name_or_animation.lower() == "thinking":
            if animation_player: animation_player.post.run("animations/Stand/BodyTalk/Thinking_1")
    except Exception as e: logging.error(f"Error performing gesture '{gesture_name_or_animation}': {e}")


def handle_function_call_from_llm(fn_call_data: Dict[str, Any]): 
    if not session or not session.isConnected(): return
    name = fn_call_data.get("name")
    args = fn_call_data.get("arguments", {}) 
    logging.info(f"Handling function call from LLM: {name} with args: {args}")
    
    if name == "navigate_to":
        location = args.get("location")
        if location:
            perform_gesture("thinking"); memory.raiseEvent("NavTarget", location)
            display_on_tablet(text_to_display=f"Navigating to: {location}", show_map=True)
        else:
            if tts: tts.say("I need a destination for navigation.")
    elif name == "get_price":
        product_name = args.get("product", "").lower()
        item = next((i for i in menu_items if i["name"].lower() == product_name), None)
        reply = f"Price for {product_name} not found."
        image_to_show = None
        if item: reply = f"{item['name']} costs €{item.get('price', 'N/A')}."; image_to_show = item.get("image_url")
        if tts: tts.say(reply); display_on_tablet(text_to_display=reply, image_url=image_to_show)
    elif name == "get_allergens":
        product_name = args.get("product", "").lower()
        item = next((i for i in menu_items if i["name"].lower() == product_name), None)
        reply = f"Allergens for {product_name} not found."
        if item: allergens = item.get("allergens", []); reply = f"{item['name']} allergens: {', '.join(allergens) if allergens else 'None listed'}."
        if tts: tts.say(reply); display_on_tablet(text_to_display=reply)
    else:
        if tts: tts.say(f"I'm not familiar with the action: {name}.")


def process_user_query_combined(query_text: str):
    global CURRENT_USER_ROLE, LISTENING_ACTIVE, LAST_INTERACTION_TIME
    
    if not tts or not session or not session.isConnected():
        logging.error("TTS/Session not available for query processing.")
        LISTENING_ACTIVE = False
        return

    LAST_INTERACTION_TIME = time.time()
    perform_gesture("thinking")

    session_status_val = "first_interaction" if CURRENT_USER_ROLE == "unknown" else "ongoing_interaction"
    
    payload = {
        "text": query_text,
        "session_status": session_status_val,
        "current_role": CURRENT_USER_ROLE
    }
    
    logging.info(f"Sending query to LLM (combined mode): {payload}")
    start_time = time.time()

    try:
        response = requests.post(LLM_SERVER_URL, json=payload, timeout=15.0)
        response.raise_for_status()
        llm_data = response.json() 

        determined_role = llm_data.get("determined_role", "customer").lower()
        response_type = llm_data.get("response_type")
        reply_content = llm_data.get("content", "").strip()
        function_call_dict = llm_data.get("function_call") 

        if CURRENT_USER_ROLE == "unknown" and determined_role in ['customer', 'worker', 'supervisor']:
            CURRENT_USER_ROLE = determined_role
            logging.info(f"Role determined by LLM as: {CURRENT_USER_ROLE}")
            if tts and session_status_val == "first_interaction":
                 pass 
            if tablet: display_on_tablet(text_to_display=f"CaféBot\nRole: {CURRENT_USER_ROLE.capitalize()}\nListening...")
        
        if response_type == "function_call" and function_call_dict:
            if reply_content:
                tts.say(reply_content)
                display_on_tablet(text_to_display=reply_content)
            handle_function_call_from_llm(function_call_dict) 
        elif response_type == "content" and reply_content:
            tts.say(reply_content)
            display_on_tablet(text_to_display=reply_content)
        else:
            logging.warning(f"LLM returned an unexpected response_type or empty content: {llm_data}")
            tts.say("I'm a bit unsure how to proceed with that. Could you try again?")
            perform_gesture("shakehead")

    except requests.exceptions.Timeout:
        logging.error("LLM request (combined) timed out.")
        tts.say("I'm taking a bit longer to think. Please wait a moment.")
    except requests.exceptions.RequestException as e:
        logging.error(f"LLM request (combined) failed: {e}")
        tts.say("I'm having trouble connecting to my AI services right now.")
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        logging.error(f"Error processing LLM's JSON response: {e}. Response: {response.text if 'response' in locals() else 'No response object'}")
        tts.say("I received a response I couldn't quite understand. Let's try that again.")
    except Exception as e:
        logging.error(f"Unexpected error during combined query processing: {e}")
        tts.say("An unexpected issue occurred while I was processing your request.")
    finally:
        LISTENING_ACTIVE = False

    elapsed_time = time.time() - start_time
    logging.info(
        f"Processed: User='{query_text}' | Status='{session_status_val}' | Det.Role='{CURRENT_USER_ROLE}' | "
        f"Reply='{reply_content if 'reply_content' in locals() else 'N/A'}' | "
        f"FnCall='{function_call_dict.get('name') if 'function_call_dict' in locals() and function_call_dict else 'None'}' | Time={elapsed_time:.2f}s"
    )

def on_word_recognized_callback(key, value, message):
    global LISTENING_ACTIVE, CURRENT_USER_ROLE, LAST_INTERACTION_TIME
    if not value or len(value) < 2: return
    text, confidence = value[0], value[1]; text_lower = text.lower()
    if confidence < ASR_CONFIDENCE_THRESHOLD: return
    logging.info(f"ASR (Combined): '{text_lower}' (conf={confidence:.2f})")

    if check_session_timeout(): pass 

    if LISTENING_ACTIVE:
        if text_lower in ["stop", "fermati", "annulla", "cancel"]:
            LISTENING_ACTIVE = False; tts.say("Okay, cancelling."); reset_session_state()
            return
        elif text_lower == "menu":
            tts.say("Displaying menu."); display_on_tablet(text_to_display="Full Menu", image_url=f"{DISPLAY_URL_BASE}/static/images/menu_overview.png")
            LISTENING_ACTIVE = False; LAST_INTERACTION_TIME = time.time()
            return
        elif text_lower in ["esci", "termina", "exit", "arrivederci", "goodbye"]:
            tts.say("Goodbye!"); cleanup(); 
            return
        threading.Thread(target=process_user_query_combined, args=(text,)).start()
    
    elif WAKE_WORD in text_lower:
        query_after_wake_word = text_lower.replace(WAKE_WORD, "", 1).strip()
        LISTENING_ACTIVE = True
        perform_gesture("animations/Stand/Emotions/Neutral/Huh_1")
        greeting = "Hello! I'm CaféBot. How can I help?" if CURRENT_USER_ROLE == "unknown" else f"Yes, {CURRENT_USER_ROLE}?"
        tts.say(greeting)
        logging.info(f"Wake word. Role: '{CURRENT_USER_ROLE}'. Query part: '{query_after_wake_word}'")
        if query_after_wake_word:
            threading.Thread(target=process_user_query_combined, args=(query_after_wake_word,)).start()
        else:
            LAST_INTERACTION_TIME = time.time()


if __name__ == "__main__":
    if not session or not session.isConnected():
        logging.critical("Pepper LLM Bridge (Combined) cannot start: Naoqi session not available.")
    else:
        logging.info(f"Pepper LLM Bridge (Combined Mode) running. Say '{WAKE_WORD}' to interact.")
        print(f"Pepper LLM Bridge (Combined Mode) running. Say '{WAKE_WORD}' to interact.")
        reset_session_state()

        try:
            word_recognized_subscriber = memory.subscriber("WordRecognized")
            id_event_word_recognized = word_recognized_subscriber.signal.connect(on_word_recognized_callback)
            logging.info("Successfully subscribed to WordRecognized event (Combined Mode).")
            try:
                while True: time.sleep(5)
            except KeyboardInterrupt: logging.info("KeyboardInterrupt. Shutting down...")
            finally:
                logging.info("Final cleanup (Combined Mode)...")
                if 'id_event_word_recognized' in locals() and word_recognized_subscriber : word_recognized_subscriber.signal.disconnect(id_event_word_recognized)
                cleanup()
                logging.info("Bridge (Combined Mode) shut down.")
        except Exception as e:
            logging.critical(f"Failed in main loop (Combined Mode): {e}")
            cleanup()
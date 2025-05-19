import qi
import requests
import json
import threading
import time
import logging
from urllib.parse import quote
import os

PEPPER_IP = os.getenv("PEPPER_IP", "127.0.0.1")
PEPPER_PORT = int(os.getenv("PEPPER_PORT", 9559))
LLM_SERVER_URL = os.getenv("LLM_SERVER_URL", "http://localhost:8000/chat")
DISPLAY_URL_BASE = os.getenv("DISPLAY_URL_BASE", "http://localhost:8000")

ASR_VERY_LOW_CONF_THRESHOLD = float(os.getenv("ASR_VERY_LOW_CONF_THRESHOLD", 0.20)) 
ASR_ASK_REPEAT_THRESHOLD = float(os.getenv("ASR_ASK_REPEAT_THRESHOLD", 0.40))   
ASR_ACCEPTABLE_CONF_THRESHOLD = float(os.getenv("ASR_ACCEPTABLE_CONF_THRESHOLD", 0.45))

WAKE_WORD = os.getenv("WAKE_WORD", "pepper").lower()

CURRENT_USER_ROLE = "unknown"
SESSION_TIMEOUT_SECONDS = 300
LAST_INTERACTION_TIME = time.time()
CURRENT_LANGUAGE = "English"

CONSECUTIVE_ASR_FAILURES = 0
MAX_ASR_FAILURES_BEFORE_RESET = 2

try:
    with open("menu.json", "r", encoding="utf-8") as f:
        menu_items = json.load(f)
except FileNotFoundError:
    menu_items = []
    logging.warning("menu.json not found. Product related functions might be limited.")

logging.basicConfig(
    filename="pepper_llm_bridge.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s"
)

session = None
tts, motion, tablet, memory, asr, awareness, posture, animation_player = (None,) * 8
ROBOT_IS_SPEAKING = False 

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
    base_vocabulary = [WAKE_WORD, "stop", "menu", "exit", "goodbye", "thanks", "yes", "no", "ok", "repeat", "sorry", "i don't understand", "help"]
    asr.setVocabulary(list(set(base_vocabulary)), True)
    asr.subscribe("CafeBotASR_ErrorHandling")

    if awareness:
        awareness.setEnabled(True); awareness.setStimulusDetectionEnabled("Sound", True)
        awareness.setTrackingMode("Head"); awareness.setEngagementMode("SemiEngaged")
    logging.info("NAOqi services initialized for error handling mode.")

except RuntimeError as e:
    logging.critical(f"CRITICAL: Cannot connect to Naoqi. Error: {e}")
except Exception as e:
    logging.error(f"Error initializing Naoqi services: {e}")


LISTENING_ACTIVE = False

def simple_say(text_to_say: str):
    global ROBOT_IS_SPEAKING
    if not tts:
        logging.warning("TTS service not available for simple_say.")
        return
    
    ROBOT_IS_SPEAKING = True
    logging.info(f"Robot SAYING (simple): '{text_to_say}'")
    try:
        tts.say(text_to_say)
    except Exception as e:
        logging.error(f"Error during tts.say in simple_say: {e}")
    finally:
        ROBOT_IS_SPEAKING = False

def reset_session_state():
    global CURRENT_USER_ROLE, LAST_INTERACTION_TIME, CONSECUTIVE_ASR_FAILURES
    logging.info(f"Resetting session state. Previous role: {CURRENT_USER_ROLE}")
    CURRENT_USER_ROLE = "unknown"
    LAST_INTERACTION_TIME = time.time()
    CONSECUTIVE_ASR_FAILURES = 0
    if tablet: display_on_tablet(text_to_display=f"CaféBot Ready\nRole: Waiting...\nSay '{WAKE_WORD}'")

def check_session_timeout():
    if CURRENT_USER_ROLE != "unknown":
        if (time.time() - LAST_INTERACTION_TIME) > SESSION_TIMEOUT_SECONDS:
            logging.info("Session timed out due to inactivity.")
            simple_say("It's been a while. Let's start fresh if you need anything.")
            reset_session_state()
            return True
    return False

def cleanup():
    global LISTENING_ACTIVE, ROBOT_IS_SPEAKING
    LISTENING_ACTIVE = False
    ROBOT_IS_SPEAKING = False 
    logging.info("Cleanup initiated.")
    if asr and session and session.isConnected():
        try: asr.unsubscribe("CafeBotASR_ErrorHandling")
        except Exception as e: logging.error(f"Error unsubscribing ASR: {e}")
    if awareness and session and session.isConnected():
        try: awareness.setEnabled(False)
        except Exception as e: logging.error(f"Error disabling awareness: {e}")
    if tablet and session and session.isConnected():
        try: tablet.hideWebview()
        except Exception as e: logging.error(f"Error hiding webview: {e}")
    if motion and posture and session and session.isConnected():
        try:
            motion.rest()
        except Exception as e: logging.error(f"Error resting robot: {e}")
    simple_say("Goodbye for now!")


def display_on_tablet(text_to_display=None, image_url=None, show_map=False, options=None):
    if not tablet or not session or not session.isConnected(): return
    base_tablet_url = f"{DISPLAY_URL_BASE}/tablet_view" 
    params = []
    if text_to_display: params.append(f"text={quote(text_to_display)}")
    if image_url: params.append(f"image={quote(image_url)}")
    if show_map: params.append(f"map=true")
    if options and isinstance(options, list):
        for opt_val in options: params.append(f"options={quote(opt_val)}") 
    final_url = base_tablet_url + (("?" + "&".join(params)) if params else "")
    try:
        logging.debug(f"Requesting tablet URL: {final_url}")
        tablet.showWebview(final_url)
    except Exception as e: logging.error(f"Error displaying on tablet: {e}. URL: {final_url}")

def perform_gesture(gesture_name_or_animation: str):
    if not motion or not animation_player or not session or not session.isConnected(): return
    logging.debug(f"Performing gesture (basic): {gesture_name_or_animation}")
    try:
        if gesture_name_or_animation.lower() == "thinking":
            if animation_player.getInstalledBehaviors().count("animations/Stand/BodyTalk/Thinking_1") > 0:
                animation_player.post.run("animations/Stand/BodyTalk/Thinking_1")
    except Exception as e: logging.error(f"Error performing basic gesture '{gesture_name_or_animation}': {e}")


def handle_function_call_from_llm(fn_call_data: Dict[str, Any]): 
    if not session or not session.isConnected(): return
    name = fn_call_data.get("name")
    args = fn_call_data.get("arguments", {}) 
    logging.info(f"Handling function call (error handling context): {name} with args: {args}")
    
    if name == "navigate_to":
        location = args.get("location")
        if location:
            memory.raiseEvent("NavTarget", location)
            # display_on_tablet(text_to_display=f"Navigating to: {location}", show_map=True)
        else:
            simple_say("I need a destination for navigation.")
    elif name == "get_price":
        product_name = args.get("product", "").lower()
        item = next((i for i in menu_items if i["name"].lower() == product_name), None)
        reply = f"Price for {product_name} not found."
        # image_to_show = None
        if item: reply = f"{item['name']} costs €{item.get('price', 'N/A')}." #; image_to_show = item.get("image_url")
        simple_say(reply)
        # display_on_tablet(text_to_display=reply, image_url=image_to_show)
    elif name == "get_allergens":
        product_name = args.get("product", "").lower()
        item = next((i for i in menu_items if i["name"].lower() == product_name), None)
        reply = f"Allergens for {product_name} not found."
        if item: allergens = item.get("allergens", []); reply = f"{item['name']} allergens: {', '.join(allergens) if allergens else 'None listed'}."
        simple_say(reply)
        # display_on_tablet(text_to_display=reply)
    else:
        simple_say(f"I'm not familiar with the action: {name}.")


def process_user_query_combined(query_text: str):
    global CURRENT_USER_ROLE, LISTENING_ACTIVE, LAST_INTERACTION_TIME, CONSECUTIVE_ASR_FAILURES
    
    if not session or not session.isConnected():
        logging.error("Session not available. Cannot process query.")
        LISTENING_ACTIVE = False
        return

    LAST_INTERACTION_TIME = time.time()
    perform_gesture("thinking")

    session_status_val = "first_interaction" if CURRENT_USER_ROLE == "unknown" else "ongoing_interaction"
    payload = {"text": query_text, "session_status": session_status_val, "current_role": CURRENT_USER_ROLE}
    
    logging.info(f"Sending query to LLM (error handling mode): {payload}")
    start_time = time.time()
    llm_response_for_log = None

    try:
        response = requests.post(LLM_SERVER_URL, json=payload, timeout=15.0)
        llm_response_for_log = response.text 
        response.raise_for_status()
        llm_data = response.json() 

        CONSECUTIVE_ASR_FAILURES = 0 

        determined_role = llm_data.get("determined_role", "customer").lower()
        response_type = llm_data.get("response_type")
        reply_content = llm_data.get("content", "").strip()
        function_call_dict = llm_data.get("function_call") 

        if CURRENT_USER_ROLE == "unknown" and determined_role in ['customer', 'worker', 'supervisor']:
            CURRENT_USER_ROLE = determined_role
            logging.info(f"Role determined by LLM as: {CURRENT_USER_ROLE}")
            # if tablet: display_on_tablet(text_to_display=f"CaféBot\nRole: {CURRENT_USER_ROLE.capitalize()}\nListening...")
        
        if response_type == "function_call" and function_call_dict:
            if reply_content:
                simple_say(reply_content)
            handle_function_call_from_llm(function_call_dict) 
        elif response_type == "content" and reply_content:
            simple_say(reply_content)
        elif not reply_content and not function_call_dict:
            logging.warning(f"LLM returned no content and no function call. Query: '{query_text}'")
            simple_say("I'm not quite sure how to help with that. Could you try asking in a different way, perhaps?")
        else: 
            logging.error(f"LLM returned an unexpected or incomplete JSON structure: {llm_data}")
            simple_say("I received a slightly confusing response. Could we try that again, please?")

    except requests.exceptions.Timeout:
        logging.error("LLM request (combined) timed out.")
        simple_say("I'm taking a bit too long to think about that. Could you try asking again in a moment?")
    except requests.exceptions.RequestException as e:
        logging.error(f"LLM request (combined) failed: {e}")
        simple_say("I'm having some trouble connecting to my AI services right now. Please try again soon.")
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        logging.error(f"Error processing LLM's JSON response: {e}. Raw Response: {llm_response_for_log}")
        simple_say("I seem to have received a muddled response from my brain. Could you please rephrase your question?")
    except Exception as e:
        logging.error(f"Unexpected error during combined query processing: {e}")
        simple_say("An unexpected issue occurred while I was processing that. My apologies.")
    finally:
        LISTENING_ACTIVE = False 

    elapsed_time = time.time() - start_time
    logging.info(
        f"Processed: User='{query_text}' | Status='{session_status_val}' | Det.Role='{CURRENT_USER_ROLE}' | Time={elapsed_time:.2f}s"
    )

def on_word_recognized_callback(key, value, message):
    global LISTENING_ACTIVE, CURRENT_USER_ROLE, LAST_INTERACTION_TIME, CONSECUTIVE_ASR_FAILURES, ROBOT_IS_SPEAKING
    
    if ROBOT_IS_SPEAKING:
        logging.info("ASR: Word recognized while robot speaking, ignoring (basic barge-in).")
        return

    if not value or not value[0]:
        logging.info(f"ASR: Recognized empty string or invalid value: {value}")
        if LISTENING_ACTIVE: 
            CONSECUTIVE_ASR_FAILURES += 1
            logging.warning(f"ASR Failure {CONSECUTIVE_ASR_FAILURES}/{MAX_ASR_FAILURES_BEFORE_RESET} (empty recognition).")
            if CONSECUTIVE_ASR_FAILURES >= MAX_ASR_FAILURES_BEFORE_RESET:
                simple_say("I'm still having trouble understanding. Let's pause for now. Please say the wake word if you need me later.")
                reset_session_state()
                LISTENING_ACTIVE = False
            else:
                simple_say("I didn't catch that. Could you please say it again a bit louder?")
            LAST_INTERACTION_TIME = time.time()
        return 

    text, confidence = value[0], value[1]; text_lower = text.lower()

    if confidence < ASR_VERY_LOW_CONF_THRESHOLD:
        logging.info(f"ASR: '{text_lower}' (conf={confidence:.2f}) - Very low confidence, considered noise. Ignored.")
        return
    
    logging.info(f"ASR (Error Handling Mode): '{text_lower}' (conf={confidence:.2f})")

    if check_session_timeout():
        pass 

    if LISTENING_ACTIVE:
        if confidence < ASR_ACCEPTABLE_CONF_THRESHOLD:
            logging.warning(f"ASR: Low confidence for command '{text_lower}' (conf={confidence:.2f}). Asking to repeat.")
            CONSECUTIVE_ASR_FAILURES += 1
            logging.warning(f"ASR Failure {CONSECUTIVE_ASR_FAILURES}/{MAX_ASR_FAILURES_BEFORE_RESET} (low confidence command).")
            if CONSECUTIVE_ASR_FAILURES >= MAX_ASR_FAILURES_BEFORE_RESET:
                simple_say("I'm really struggling to understand your commands. Let's try resetting. Say the wake word when you're ready.")
                reset_session_state()
                LISTENING_ACTIVE = False
            else:
                simple_say("Sorry, I'm not quite sure I got that command clearly. Could you please repeat it for me?")
            LAST_INTERACTION_TIME = time.time()
            return

        if text_lower in ["stop", "fermati", "annulla", "cancel"]:
            LISTENING_ACTIVE = False; simple_say("Okay, cancelling that."); reset_session_state()
            return
        elif text_lower == "menu":
            simple_say("Showing the menu information now.")
            # display_on_tablet(text_to_display="Full Menu Information...")
            LISTENING_ACTIVE = False; LAST_INTERACTION_TIME = time.time()
            return
        elif text_lower in ["esci", "termina", "exit", "arrivederci", "goodbye"]:
            simple_say("Goodbye! Have a great day."); cleanup()
            # threading.Timer(2.0, lambda: os._exit(0)).start() 
            return
        
        threading.Thread(target=process_user_query_combined, args=(text,)).start()
    
    elif WAKE_WORD in text_lower:
        if confidence < ASR_ACCEPTABLE_CONF_THRESHOLD:
            logging.warning(f"ASR: Low confidence for wake word phrase '{text_lower}' (conf={confidence:.2f}). Ignoring.")
            return

        CONSECUTIVE_ASR_FAILURES = 0
        query_after_wake_word = text_lower.replace(WAKE_WORD, "", 1).strip()
        LISTENING_ACTIVE = True
        
        perform_gesture("thinking")
        
        greeting = "Hello! I'm CaféBot. How can I help?" if CURRENT_USER_ROLE == "unknown" else f"Yes, {CURRENT_USER_ROLE}?"
        time.sleep(0.2)
        simple_say(greeting)
        
        logging.info(f"Wake word detected. Role: '{CURRENT_USER_ROLE}'. Query part: '{query_after_wake_word}'")
        if query_after_wake_word:
            threading.Thread(target=process_user_query_combined, args=(query_after_wake_word,)).start()
        else:
            LAST_INTERACTION_TIME = time.time()
            logging.info("Awaiting command after wake word...")


if __name__ == "__main__":
    if not session or not session.isConnected():
        logging.critical("Pepper LLM Bridge (Error Handling) cannot start: Naoqi session is not available.")
    else:
        logging.info(f"Pepper LLM Bridge (Error Handling Mode) running. Say '{WAKE_WORD}' to interact.")
        print(f"Pepper LLM Bridge (Error Handling Mode) running. Say '{WAKE_WORD}' to interact.")
        reset_session_state() 
        simple_say("Hello, I'm CafeBot, How can i help you today?")

        try:
            word_recognized_subscriber = memory.subscriber("WordRecognized")
            id_event_word_recognized = word_recognized_subscriber.signal.connect(on_word_recognized_callback)
            logging.info("Successfully subscribed to WordRecognized event (Error Handling Mode).")

            try:
                while True: 
                    time.sleep(1)
                    if not LISTENING_ACTIVE and not ROBOT_IS_SPEAKING and (time.time() - LAST_INTERACTION_TIME > 30):
                        logging.debug("Idle state check.")
                        LAST_INTERACTION_TIME = time.time()
            except KeyboardInterrupt: 
                logging.info("KeyboardInterrupt received. Shutting down...")
            finally:
                logging.info("Initiating final cleanup (Error Handling Mode)...")
                if 'id_event_word_recognized' in locals() and word_recognized_subscriber and word_recognized_subscriber.signal.isConnected(id_event_word_recognized):
                    try: word_recognized_subscriber.signal.disconnect(id_event_word_recognized)
                    except Exception as e: logging.error(f"Error disconnecting from WordRecognized signal: {e}")
                cleanup() 
                logging.info("Pepper LLM Bridge (Error Handling Mode) shut down.")
                print("Pepper LLM Bridge (Error Handling Mode) shut down.")
        except Exception as e:
            logging.critical(f"Failed in main loop (Error Handling Mode): {e}")
            cleanup()
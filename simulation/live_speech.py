import speech_recognition as sr

r = sr.Recognizer()
r.pause_threshold = 0.8 
r.energy_threshold = 300

def listen_for_input(prompt="Listening..."):
    with sr.Microphone() as source:
        print(f"[Speech] {prompt}")
        
        r.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            print("[Speech] Timeout: No speech detected.")
            return None

    try:
        print("[Speech] Recognizing...")
        recognized_text = r.recognize_google(audio, language="en-US, it-IT")
        print(f"[Speech] Recognized: '{recognized_text}'")
        return recognized_text.lower()
    except sr.UnknownValueError:
        print("[Speech] Could not understand the audio.")
        return None
    except sr.RequestError as e:
        print(f"[Speech] Could not request results from Google Speech Recognition service; {e}")
        return None
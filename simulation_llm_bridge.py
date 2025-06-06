import requests
import json
import numpy as np
from simulation import say_simulation, motion_simulation

LLM_SERVER_URL = "http://localhost:8000/chat"


session_state = {
    "current_role": "unknown",
    "session_status": "first_interaction"
}

def reset_session():
    print("[Bridge] Session reset. Waiting for a new first interaction.")
    session_state["current_role"] = "unknown"
    session_state["session_status"] = "first_interaction"

def process_user_command(text_command):
    print(f"\n[Bridge] Sending command to LLM: '{text_command}' (State: {session_state['session_status']}, Role: {session_state['current_role']})")
    payload = {
        "text": text_command,
        "session_status": session_state["session_status"],
        "current_role": session_state["current_role"]
    }
    try:
        response = requests.post(LLM_SERVER_URL, json=payload, timeout=20.0)
        response.raise_for_status()
        llm_data = response.json()
        session_state["current_role"] = llm_data.get("determined_role", "customer")
        session_state["session_status"] = "ongoing_interaction"
        print(f"[Bridge] Response received from LLM: {llm_data}")
        return llm_data
    except requests.exceptions.RequestException as e:
        print(f"[Bridge] ERROR: Could not communicate with LLM server. {e}")
        return None

def handle_llm_response(pepper, response_data, dynamic_map, menu_data, ignored_ids=[]):
    if not response_data:
        say_simulation.say(pepper, "Sorry, I'm having trouble connecting to my decision-making circuits.")
        return

    content_to_say = response_data.get("content")
    if response_data.get("response_type") == "function_call":
        function_generated_text = handle_function_call(pepper, response_data.get("function_call"), dynamic_map, menu_data, ignored_ids)
        if function_generated_text:
            content_to_say = function_generated_text
    
    if content_to_say:
        say_simulation.say(pepper, content_to_say)

def handle_function_call(pepper, function_call, dynamic_map, menu_data, ignored_ids):
    if not function_call: return None
    func_name = function_call.get("name")
    args = function_call.get("arguments", {})
    print(f"[Bridge] Executing function: {func_name} with arguments {args}")

    if func_name == "Maps_to":
        location_label = args.get("location", "").lower().strip()
        if not location_label: return "I did not understand the destination. Can you repeat?"
        target_coords = next((obj['world_coordinates'] for obj in dynamic_map if location_label in obj['label'].lower()), None)
        if target_coords:
            motion_simulation.moveToGoal(pepper, tuple(target_coords[:2]), ignored_ids)
            return "Ok, we have arrived at the destination."
        return f"I'm sorry, I looked around but I can't find {location_label}."
    
    elif func_name == "get_price":
        product_name = args.get("product", "").lower().strip()
        item = next((item for item in menu_data if product_name in item["name"].lower()), None)
        return f"The price of {item['name']} is {item.get('price', 'unknown')} euros." if item else f"I could not find price information for {product_name}."

    elif func_name == "get_allergens":
        product_name = args.get("product", "").lower().strip()
        item = next((item for item in menu_data if product_name in item["name"].lower()), None)
        if item:
            allergens = item.get("allergens", [])
            return f"The allergens for {item['name']} are: {', '.join(allergens)}." if allergens else f"There are no specified allergens for {item['name']}."
        return f"I could not find allergen information for {product_name}."
        
    return "I am not yet able to perform this action."
import requests
import json
from simulation import say_simulation
from simulation.motion_simulation_dynamic import moveToGoalDynamic
from simulation.perception import PerceptionModule

LLM_SERVER_URL = "http://localhost:8000/chat"

session_state = {
    "current_role": "unknown",
    "session_status": "first_interaction"
}

_perceptor = PerceptionModule()

def reset_session():

    print("[Bridge] Session reset.")
    session_state["current_role"] = "unknown"
    session_state["session_status"] = "first_interaction"

def process_user_command(text_command):

    print(f"[Bridge] → LLM: '{text_command}' "
          f"({session_state['session_status']}, {session_state['current_role']})")
    payload = {
        "text": text_command,
        "session_status": session_state["session_status"],
        "current_role": session_state["current_role"]
    }
    try:
        response = requests.post(LLM_SERVER_URL, json=payload, timeout=20.0)
        response.raise_for_status()
        data = response.json()
        session_state["current_role"] = data.get("determined_role", "customer")
        session_state["session_status"] = "ongoing_interaction"
        print(f"[Bridge] ← LLM: {data}")
        return data
    except requests.RequestException as e:
        print(f"[Bridge] ERROR contacting LLM: {e}")
        return None

def handle_llm_response(pepper, response_data, dynamic_map, menu_data, ignored_ids):
    
    _perceptor.update_semantic_map(pepper)

    if not response_data:
        say_simulation.say(pepper,
            "Sorry, I'm having trouble connecting to my decision circuits.")
        return

    if response_data.get("response_type") == "function_call":
        result_text = handle_function_call(
            pepper,
            response_data["function_call"],
            dynamic_map,
            menu_data,
            ignored_ids
        )
        if result_text:
            say_simulation.say(pepper, result_text)
    else:
        content = response_data.get("content")
        if content:
            say_simulation.say(pepper, content)

def handle_function_call(pepper, function_call, dynamic_map, menu_data, ignored_ids):
 
    name = function_call.get("name")
    args = function_call.get("arguments", {})

    if name == "Maps_to":
        loc = args.get("location", "").lower().strip()
        if not loc:
            return "I did not understand the destination. Could you repeat?"

        coords = next(
            ((x, y) for obj in dynamic_map
             for label, x, y, z in [(obj["label"], *obj["world_coordinates"])]
             if loc in label.lower()),
            None
        )
        if coords:
            moveToGoalDynamic(pepper, coords)
            return f"Okay, I've arrived at the {loc}."
        else:
            return f"Sorry, I couldn't find any {loc} nearby."

    elif name == "get_price":
        prod = args.get("product", "").lower().strip()
        item = next((i for i in menu_data
                     if prod in i["name"].lower()), None)
        if item:
            return f"The price of {item['name']} is {item['price']} euros."
        else:
            return f"I could not find price information for {prod}."

    elif name == "get_allergens":
        prod = args.get("product", "").lower().strip()
        item = next((i for i in menu_data
                     if prod in i["name"].lower()), None)
        if item:
            alls = item.get("allergens", [])
            if alls:
                return f"The allergens for {item['name']} are: {', '.join(alls)}."
            else:
                return f"There are no specified allergens for {item['name']}."
        else:
            return f"I could not find allergen information for {prod}."

    else:
        return "I'm not yet able to perform that action."
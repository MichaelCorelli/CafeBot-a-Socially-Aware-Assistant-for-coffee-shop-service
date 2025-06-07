import os
import json
from dotenv import load_dotenv
import openai
import faiss
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from typing import Literal, Optional, Dict, Any


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMB_MODEL = os.getenv("EMB_MODEL", "text-embedding-3-small")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. Check your .env file.")

openai.api_key = OPENAI_API_KEY

SYSTEM_PROMPT = (
    "You are CaféBot, an advanced, multilingual service robot in an Italian coffee shop. "
    "Your primary goal is to provide efficient and appropriate assistance. "
    "You interact with three distinct user types: Customers, Workers, and Supervisors. "
    "ALL your textual responses to the user MUST be concise, ideally under 20 words. "
    "Always respond in the user's language (Italian or English).\n\n"
    
    "**Interaction Flow & Output Format:**\n"
    "You will receive a `session_status` field indicating if this is a 'first_interaction' (user role is unknown) "
    "or an 'ongoing_interaction' (user role is known and provided as `current_role`).\n"
    "Your entire response MUST be a single JSON object. Do NOT include any text outside this JSON object.\n"
    "The JSON object must have the following structure:\n"
    "{\n"
    "  \"determined_role\": \"<role>\",\n"
    "  \"response_type\": \"content\" | \"function_call\",\n"
    "  \"content\": \"<textual_response_to_user_if_any>\",\n"
    "  \"function_call\": null | { \"name\": \"<function_name>\", \"arguments\": { \"<arg_name>\": \"<arg_value>\", ... } }\n"
    "}\n\n"
    
    "**Detailed Instructions based on `session_status`:**\n\n"

    "1.  **IF `session_status` IS 'first_interaction':**\n"
    "    a.  **Infer User Role:** Analyze the user's query to determine if they are a 'customer', 'worker', or 'supervisor'.\n"
    "        * **Customer cues:** Informal language, queries about products, prices, general locations (e.g., 'Where is...', 'How much is...').\n"
    "        * **Worker cues:** Direct language, queries about stock, operational tasks, specific product details for service (e.g., 'Stock level for milk?', 'Espresso machine status?').\n"
    "        * **Supervisor cues:** Formal language, queries about performance, reports, staff, overall status (e.g., 'Today's sales figures?', 'Incident report?').\n"
    "        * If ambiguous, default to 'customer'.\n"
    "        * Set the `determined_role` field in the output JSON to the inferred role (e.g., \"customer\", \"worker\", \"supervisor\").\n"
    "    b.  **Generate Response/Function Call:** Based on the user's query AND the role you just inferred, formulate the appropriate textual response or function call.\n"
    "        Follow the persona guidelines for the inferred role (detailed below).\n"
    "        Populate `response_type`, `content`, and `function_call` fields in the output JSON accordingly.\n\n"

    "2.  **IF `session_status` IS 'ongoing_interaction':**\n"
    "    a.  **Use Provided Role:** The user's role (`current_role`) is already known and provided to you.\n"
    "        Set the `determined_role` field in the output JSON to this `current_role`.\n"
    "    b.  **Generate Response/Function Call:** Based on the user's query AND this known `current_role`, formulate the appropriate textual response or function call.\n"
    "        Follow the persona guidelines for this role (detailed below).\n"
    "        Populate `response_type`, `content`, and `function_call` fields in the output JSON accordingly.\n\n"

    "**User Role Persona & Tone Guidelines (to be applied once role is determined):**\n\n"

    "1.  **Customer Interaction:**\n"
    "    * **Tone:** Very friendly, welcoming, enthusiastic, and highly helpful. Use simple, clear language. "
    "        Always offer a warm greeting or closing. Prioritize customer satisfaction.\n"
    "    * **Content Focus:** Address immediate needs, provide product information (price, location, basic description from context), "
    "        and guide them. Keep it light and positive.\n"
    "    * **Example Query (Location):** 'Where's the restroom?'\n"
    "        * **CaféBot Response (Customer):** 'Hello! The restroom is just past the counter, on your right. Let me know if you need more help!'\n"
    "    * **Example Query (Price):** 'How much is a cappuccino?'\n"
    "        * **CaféBot Response (Customer):** 'A cappuccino is €1.50. Enjoy your coffee!'\n\n"

    "2.  **Worker Interaction:**\n"
    "    * **Tone:** Direct, concise, professional, and task-oriented. Use efficient language. Assume shared operational knowledge. "
    "        Avoid chit-chat.\n"
    "    * **Content Focus:** Provide specific operational data (e.g., stock levels if available in context, product details for tasks), "
    "        confirm actions, or relay information succinctly. Use internal jargon/codes if provided in context or relevant.\n"
    "    * **Example Query (Location):** 'Restroom location check.'\n"
    "        * **CaféBot Response (Worker):** 'Restroom: corridor right, past counter. Sector C-2. Clear.'\n"
    "    * **Example Query (Info):** 'Cappuccino, details for order.'\n"
    "        * **CaféBot Response (Worker):** 'Cappuccino: €1.50. Standard prep. Stock: 20 units. Item ID: item-001.'\n\n"

    "3.  **Supervisor Interaction:**\n"
    "    * **Tone:** Formal, respectful, objective, and data-driven. Present information clearly and methodically.\n"
    "    * **Content Focus:** Report status, provide summaries, and include Key Performance Indicators (KPIs) or relevant metrics if available in the context. "
    "        Focus on efficiency, compliance, and strategic data points.\n"
    "    * **Example Query (Location Status):** 'Status report for restroom accessibility.'\n"
    "        * **CaféBot Response (Supervisor):** 'Restroom accessible, Sector C-2. Last maintenance: 08:00. No issues reported.'\n"
    "    * **Example Query (Product Performance):** 'Cappuccino performance overview.'\n"
    "        * **CaféBot Response (Supervisor):** 'Cappuccino: €1.50. Sales (today): 45 units. Current stock: 20. Profit margin: X%.' (Note: some data like profit margin might not be in current context)\n\n"

    "**Function Call Definitions (if `response_type` is 'function_call'):**\n"
    "   - `Maps_to`: Arguments: `{\"location\": \"<semantic_name>\"}`. For guiding to areas or products.\n"
    "   - `get_price`: Arguments: `{\"product\": \"<product_name>\"}`. For product prices.\n"
    "   - `get_allergens`: Arguments: `{\"product\": \"<product_name>\"}`. For allergen info.\n"
    "   If a function call is appropriate, the `content` field in the JSON can be a short confirmation (e.g., 'Okay, navigating now.') or empty, but the `function_call` field MUST be populated correctly.\n\n"
    
    "**General Rules for Response Content (if `response_type` is 'content'):**\n"
    "* Textual responses must be under 20 words.\n"
    "* Use clear directional cues (left/right/ahead/behind) if giving directions textually.\n"
    "* If information is missing for a full answer, politely state what you can provide or ask a concise clarifying question.\n"
    "* Always respond in the user's original language (Italian or English).\n\n"
    "Remember: Your entire output must be a single, valid JSON object as specified."
)


#KNOWLEDGE BASE (FAISS)
index = None
docs = []
try:
    with open("menu.json", "r", encoding="utf-8") as f:
        menu_items = json.load(f)
    docs = [json.dumps(item, ensure_ascii=False) for item in menu_items]

    if docs:
        print("Generating embeddings for knowledge base…")
        emb_res = openai.Embeddings.create(input=docs, model=EMB_MODEL)
        embs = [d.embedding for d in emb_res.data]
        dims = len(embs[0])
        index = faiss.IndexFlatL2(dims)
        index.add(np.array(embs, dtype="float32"))
        print(f"FAISS index created with {len(docs)} documents.")
    else:
        print("menu.json is empty or not found. Knowledge base will be unavailable.")

except FileNotFoundError:
    print("WARNING: menu.json not found. Knowledge base will be unavailable.")
except Exception as e:
    print(f"Error initializing FAISS knowledge base: {e}")
    index = None

#PYDANTIC MODELS
class Utterance(BaseModel):
    text: str
    session_status: Literal['first_interaction', 'ongoing_interaction']
    current_role: Optional[Literal['customer', 'worker', 'supervisor', 'unknown']] = 'unknown'

class FunctionCallArgs(BaseModel):
    location: Optional[str] = None
    product: Optional[str] = None

class FunctionCall(BaseModel):
    name: str
    arguments: FunctionCallArgs

class LLMResponse(BaseModel):
    determined_role: Literal['customer', 'worker', 'supervisor']
    response_type: Literal['content', 'function_call']
    content: Optional[str] = None
    function_call: Optional[FunctionCall] = None
    
#FASTAPI APP
app = FastAPI()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
@app.post("/chat", response_model=LLMResponse)
async def chat(u: Utterance):
    context = ""
    if index and docs:
        try:
            q_res = openai.Embeddings.create(input=[u.text], model=EMB_MODEL)
            q_emb = q_res.data[0].embedding
            k = min(3, len(docs))
            _, I = index.search(np.array([q_emb], dtype="float32"), k)
            context = "\n\n".join(docs[i] for i in I[0])
        except Exception as e:
            logging.error(f"Error during RAG context retrieval: {e}")

    user_message_content = f"Session status: {u.session_status}.\n"
    if u.session_status == 'ongoing_interaction':
        user_message_content += f"Current known role: {u.current_role}.\n"
    user_message_content += f"User query: {u.text}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Retrieved Context (use if relevant):\n{context}"},
        {"role": "user", "content": user_message_content}
    ]

    try:
        logging.info(f"Sending to LLM. Messages: {json.dumps(messages, indent=2)}")
        resp = openai.ChatCompletion.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=300
            # response_format={ "type": "json_object" } # Da usare con modelli che lo supportano esplicitamente
        )
        raw_llm_output = resp.choices[0].message.get("content", "{}").strip()
        logging.info(f"Raw LLM output: {raw_llm_output}")

        try:
            parsed_output = json.loads(raw_llm_output)
            
            if not all(k in parsed_output for k in ["determined_role", "response_type"]):
                raise ValueError("LLM output missing required fields.")
            if parsed_output["determined_role"] not in ['customer', 'worker', 'supervisor']:
                 logging.warning(f"LLM returned invalid determined_role '{parsed_output['determined_role']}', defaulting to customer.")
                 parsed_output["determined_role"] = "customer" 

            llm_response_obj = LLMResponse(**parsed_output)
            logging.info(f"Successfully parsed and validated LLM response: {llm_response_obj.model_dump_json(indent=2)}")
            return llm_response_obj

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM JSON output. Error: {e}. Output: {raw_llm_output}")
            
            return LLMResponse(
                determined_role="customer",
                response_type="content",
                content="I encountered an issue processing the response structure. Please try again."
            )
        except ValueError as e:
            logging.error(f"LLM output validation error: {e}. Output: {raw_llm_output}")
            return LLMResponse(
                determined_role="customer",
                response_type="content",
                content="There was a validation error in the response I received. Please rephrase."
            )

    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        raise HTTPException(status_code=503, detail=f"OpenAI API error: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error in /chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
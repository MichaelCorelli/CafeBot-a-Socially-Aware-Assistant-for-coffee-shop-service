import os
import json
from dotenv import load_dotenv
import openai
import faiss
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMB_MODEL      = os.getenv("EMB_MODEL", "text-embedding-3-small")
LLM_MODEL      = os.getenv("LLM_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. Check your .env file.")

openai.api_key = OPENAI_API_KEY

SYSTEM_PROMPT = (
    "You are CaféBot, a courteous, multilingual service robot in an Italian coffee shop. "
    "You assist three types of users: customers, workers and supervisors, adapting tone and content accordingly:\n"
    "- **Customer**: friendly, upbeat, promotional.\n"
    "- **Worker**: concise, technical, uses internal jargon.\n"
    "- **Supervisor**: formal, data-driven, include KPIs when relevant.\n\n"
    "Always keep responses under 20 words, use clear directional cues (left/right/behind/ahead), "
    "and wrap any navigation intent in a function call:\n"
    "```json\n"
    "  \"function_call\": {\"name\": \"navigate_to\", \"arguments\": {\"location\": \"<AREA_OR_PRODUCT>\"}}\n"
    "```\n"
    "If the user asks for a product’s price or allergens, call functions `get_price` or `get_allergens` similarly. "
    "If you lack information, politely ask a follow-up question. Always respond in the user’s language (Italian or English)."
)


with open("menu.json", "r", encoding="utf-8") as f:
    menu_items = json.load(f)
docs = [json.dumps(item, ensure_ascii=False) for item in menu_items]


print("Generating embeddings for knowledge base…")
emb_res = openai.Embeddings.create(input=docs, model=EMB_MODEL)
embs = [d.embedding for d in emb_res.data]
dims = len(embs[0])
index = faiss.IndexFlatL2(dims)
index.add(np.array(embs, dtype="float32"))

app = FastAPI()

class Utterance(BaseModel):
    text: str
    role: str = "customer"

@app.post("/chat")
async def chat(u: Utterance):

    q_res = openai.Embeddings.create(input=[u.text], model=EMB_MODEL)
    q_emb = q_res.data[0].embedding
    k = min(3, len(docs))
    _, I = index.search(np.array([q_emb], dtype="float32"), k)
    context = "\n\n".join(docs[i] for i in I[0])

    messages = [
        {"role":"system",  "content": SYSTEM_PROMPT},
        {"role":"system",  "content": f"Context:\n{context}"},
        {"role":"user",    "content": u.text}
    ]

    functions = [
        {
            "name":"navigate_to",
            "description":"Navigate to a named location",
            "parameters":{
                "type":"object",
                "properties":{
                    "location":{"type":"string"}
                },
                "required":["location"]
            }
        },
        {
            "name":"get_price",
            "description":"Get price of a product",
            "parameters":{
                "type":"object",
                "properties":{
                    "product":{"type":"string"}
                },
                "required":["product"]
            }
        },
        {
            "name":"get_allergens",
            "description":"Get allergen info of a product",
            "parameters":{
                "type":"object",
                "properties":{
                    "product":{"type":"string"}
                },
                "required":["product"]
            }
        }
    ]

    resp = openai.ChatCompletion.create(
        model=LLM_MODEL,
        messages=messages,
        functions=functions,
        temperature=0.3
    )
    message = resp.choices[0].message

    result = {
        "role": message["role"],
        "content": message["content"] or ""
    }
    if message.get("function_call"):
        result["function_call"] = message["function_call"]
    return result

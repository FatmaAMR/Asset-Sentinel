import uvicorn
from fastapi import FastAPI, Body
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Get your Groq Key from .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.post("/v1/predict")
async def mock_predict(payload: dict = Body(...)):
    system_instruction = payload.get("system_instruction")
    user_input = payload.get("user_input")

    # Prepare Groq Payload
    groq_payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_input}
        ],
        "temperature": 0.1
    }
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    async with httpx.AsyncClient() as client:
        print(f"[Mock Master] Sending request to Groq for user query...")
        response = await client.post(GROQ_URL, json=groq_payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            # Wrap Groq response into our Master Service Schema
            answer = result["choices"][0]["message"]["content"]
            print(f"[Mock Master] Successfully got SQL from Groq")
            return {"generated_text": answer}
        else:
            print(f"[Mock Master] Groq Error: {response.text}")
            return {"generated_text": "Error: Could not reach Groq"}

if __name__ == "__main__":
    # This runs on 8005, exactly where your Querying Service is looking
    uvicorn.run(app, host="127.0.0.1", port=8005)
import json
from channels.generic.websocket import AsyncWebsocketConsumer
import aiohttp
from transformers import pipeline
from django.conf import settings


# Load Local LLM Model
# pipe = pipeline("text-generation", model="meta-llama/Llama-3.1-8B-Instruct")
# pipe.tokenizer.pad_token_id = pipe.model.config.eos_token_id

HF_API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
# HF_API_KEY = "your-huggingface-api-key" 


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """ Accepts WebSocket connection """
        await self.accept()
        await self.send(text_data=json.dumps({"message": "Hello! I am your AI medical assistant. How can I help you?"}))

    async def receive(self, text_data):
        """ Processes messages from frontend and responds """
        data = json.loads(text_data)
        user_message = data.get("message", "")
        user_message = f"{user_message}\nPlease provide a response with less than 300 tokens."

        print("User Message:", user_message)
        
        response = await self.query_hf_model(user_message)
        formatted_response = response.replace("\n", "\n")  # Ensures newline preservation

        print("AI Response:", response)
        
        await self.send(text_data=json.dumps({"message": formatted_response,"format": "markdown"}))

    async def disconnect(self, close_code):
        """ Handles disconnection """
        print("WebSocket Disconnected")

    async def query_hf_model(self, prompt):
        """ Queries the Hugging Face Inference API asynchronously """
        headers = {"Authorization": f"Bearer {settings.HF_API_KEY}"}
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 300}}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(HF_API_URL, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result[0]["generated_text"] if result else "Sorry, I couldn't generate a response."
                else:
                    error_message = await response.text()
                    return f"Error {response.status}: {error_message}"
               

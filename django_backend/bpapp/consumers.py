import json
from channels.generic.websocket import AsyncWebsocketConsumer
from transformers import pipeline
# from mistral_inference import MistralClient  # Import Mistral client

# # Initialize Mistral Client
# mistral_client = MistralClient(api_key="your-mistral-api-key") 

# Load Local LLM Model
pipe = pipeline("text-generation", model="meta-llama/Llama-3.2-1B")

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """ Accepts WebSocket connection """
        await self.accept()
        await self.send(text_data=json.dumps({"message": "Hello! I am your AI medical assistant. How can I help you?"}))

    async def receive(self, text_data):
        """ Processes messages from frontend and responds """
        data = json.loads(text_data)
        user_message = data["message"]

        # Generate AI response using LLM
        response = llm(f"User: {user_message}\nAI:", max_length=300)[0]["generated_text"]

        await self.send(text_data=json.dumps({"message": response}))

    async def disconnect(self, close_code):
        """ Handles disconnection """
        print("WebSocket Disconnected")

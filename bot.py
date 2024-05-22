import os
import time
import json
import asyncio
import websockets
import argparse
import google.generativeai as genai
from instructions import *

genai.configure(api_key=os.environ['GOOGLE_DEV_API_KEY'])

MODEL = "gemini-1.5-flash-latest"
DELAY = 5

class SharedChatHistory:
    def __init__(self):
        self.history = []

    def add_message(self, role, name, text):
        self.history.append({"role": role, "name": name, "text": text})

    def get_history(self):
        return self.history

    def format_history(self):
        formatted_history = []
        for entry in self.history:
            formatted_history.append(f"{entry['name']} ({entry['role']}): {entry['text']}")
        return "\n".join(formatted_history)

class AI_Teammate:
    def __init__(self, name, model_name, system_instructions, shared_history):
        print("[+] Bot got system instruction: {}".format(system_instructions[:20]))
        self.name = name
        self.model = genai.GenerativeModel(model_name, system_instruction=system_instructions)
        self.shared_history = shared_history

    def send_message(self, message, history=[]):
        time.sleep(DELAY)
        print(f"{self.name} is processing the message: {message}")

        self.chat = self.model.start_chat(history=history)
        self.shared_history.add_message("user", self.name, message)
        response = self.chat.send_message(message)
        reply = response.text
        self.shared_history.add_message("model", self.name, reply)
        print(f"{self.name} response: {reply}")
        return reply
    
    def get_history(self):
        return self.chat.history

class AIModerator:
    def __init__(self, model_name, system_instructions):
        print("[+] Mod got system instruction: {}".format(system_instructions[:20]))    
        self.model = genai.GenerativeModel(model_name, system_instruction=system_instructions)
        self.chat = self.model.start_chat()

    def determine_next_speaker(self, chat_history):
        time.sleep(DELAY)
        history_text = "\n".join([f"{entry['name']} ({entry['role']}): {entry['text']}" for entry in chat_history])
        prompt = f"Based on the following conversation, who should speak next?\n\n{history_text}\n\nRespond with ONLY the next speaker's name, e.g., \"Aristotle\""
        
        response = self.chat.send_message(prompt)
        next_speaker = response.text.strip()
        print(f"Moderator response: {next_speaker}")
        
        valid_speakers = ['Alex', 'Jordan', 'Casey', 'Riley', 'Morgan', 'Gabe']
        if next_speaker not in valid_speakers:
            print(f"Invalid speaker name returned by moderator: {next_speaker}")
            return "Gabe"  # Fallback to user if invalid response
        return next_speaker

class Bot:
    def __init__(self, _id, name, host, port, hub_uri, bot_instructions, mod_instructions):
        self._id = _id
        self.name = name
        self.host = host
        self.port = port
        self.hub_uri = hub_uri

        self.shared_history = SharedChatHistory()
        self.teammate = AI_Teammate(name=name, model_name=MODEL, system_instructions=bot_instructions, shared_history=self.shared_history)
        self.moderator = AIModerator(model_name=MODEL, system_instructions=mod_instructions)

    async def connect(self):
        async with websockets.connect(self.hub_uri) as websocket:
            # Register bot with the hub
            connect_msg = {
                "type": "ai_connect",
                "name": self.name,
                "id": self._id,
                "being": "ai",
                "host": self.host,
                "port": self.port
            }
            await websocket.send(json.dumps(connect_msg))

            async for message in websocket:
                await self.handle_message(websocket, message)

    async def handle_message(self, websocket, message_obj_str):
        message = json.loads(message_obj_str)
        msg_type = message.get("type")

        if msg_type == "msg_recvd":
            sender = message.get("from")
            msg = message.get("message")

            # Maintain chat history
            self.shared_history.add_message("user", sender, msg)

            # Moderator decides if this bot should respond
            next_speaker_name = self.moderator.determine_next_speaker(self.shared_history.get_history())

            if next_speaker_name == self.name:
                response = self.teammate.send_message(message=msg, history=self.get_history())
                response_msg = {
                    "type": "msg_recvd",
                    "from": self._id,
                    "message": response
                }
                await websocket.send(json.dumps(response_msg))

def main():
    parser = argparse.ArgumentParser(description="AI Bot")
    parser.add_argument("--id", type=str, required=True, help="Unique identifier for the bot")
    parser.add_argument("--name", type=str, required=True, help="Name of the bot")
    parser.add_argument("--host", type=str, required=True, help="Host IP address")
    parser.add_argument("--port", type=int, required=True, help="Port number")
    parser.add_argument("--hub_uri", type=str, required=True, help="WebSocket URI of the hub")
    parser.add_argument("--instruction-file", type=str, required=True, help="The txt file containing instructions for this bot")
    parser.add_argument("--moderator-instruction-file", type=str, required=True, help="The moderator instruction file")

    args = parser.parse_args()

    inst_file = args.instruction_file
    m_inst_file = args.moderator_instruction_file

    if not os.path.exists(inst_file):
        print("[!] Instruction file {} does not exist!".format(inst_file))
        exit(-1)
    if not os.path.exists(m_inst_file):
        print("[!] Moderator instruction file {} does not exist!".format(m_inst_file))

    with open(inst_file, "r") as f:
        inst = f.read()

    with open(m_inst_file, "r") as f:
        m_inst = f.read()

    bot = Bot(_id=args.id, name=args.name, host=args.host, port=args.port, hub_uri=args.hub_uri, bot_instructions=inst, mod_instructions=m_inst)

    asyncio.run(bot.connect())

if __name__ == "__main__":
    main()

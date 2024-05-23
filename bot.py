import os
import json
import asyncio
import websockets
import argparse
import logging
import google.generativeai as genai
from google.generativeai.types import content_types

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='bot.log', filemode='a')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)

genai.configure(api_key=os.environ['GOOGLE_DEV_API_KEY'])

MODEL = "gemini-1.5-flash-latest"
DELAY = 5
PROCESSING_INTERVAL = 30  # Time in seconds between processing messages
MAX_RETRIES = 5  # Maximum number of retries for WebSocket connection
KEEPALIVE_INTERVAL = 120  # Increase keepalive interval

class ConversationHistory:
    def __init__(self):
        self.history = []

    def add_message(self, role, name, text):
        self.history.append({
            "role": role,
            "name": name,
            "text": text,
            "parts": [{"text": f"[{name}] {text}"}]
        })

    def get_history(self):
        return [{"role": entry["role"], "parts": entry["parts"]} for entry in self.history]

    def get_recent_history(self, limit=10):
        return self.history[-limit:]

class AI_Teammate:
    def __init__(self, name, model_name, system_instructions, conversation_history):
        logging.info(f"[+] Bot got system instruction: {system_instructions[:20]}")
        self.name = name
        self.model = genai.GenerativeModel(model_name, system_instruction=system_instructions)
        self.conversation_history = conversation_history
        self.chat = self.model.start_chat(history=conversation_history.get_history())

    async def send_message(self, message):
        await asyncio.sleep(DELAY)
        logging.info(f"{self.name} is processing the message: {message}")

        self.conversation_history.add_message("user", self.name, message)
        response = self.chat.send_message(message)
        reply = response.text
        self.conversation_history.add_message("model", self.name, reply)
        logging.info(f"{self.name} response: {reply}")
        return reply

class AIModerator:
    def __init__(self, model_name, system_instructions, teammate_name):
        logging.info(f"[+] Mod got system instruction: {system_instructions[:20]}")
        self.model = genai.GenerativeModel(model_name, system_instruction=system_instructions)
        self.teammate_name = teammate_name
        self.chat = self.model.start_chat()

    async def should_speak_next(self, chat_history):
        await asyncio.sleep(DELAY)
        recent_history = chat_history[-10:]  # Get the last 10 messages
        history_text = "\n".join([f"{entry['parts'][0]['text']}" for entry in recent_history])
        prompt = f"Based on the following conversation, should {self.teammate_name} speak next?\n\n{history_text}\n\nRespond with YES or NO."

        response = self.chat.send_message(prompt)
        answer = response.text.strip().lower()
        logging.info(f"Moderator response: {answer}")

        if answer in ["yes", "y"]:
            return True
        elif answer in ["no", "n"]:
            return False
        else:
            logging.error(f"Invalid response from moderator: {answer}")
            return False  # Default to not speaking if the response is invalid

class Bot:
    def __init__(self, _id, name, host, port, hub_uri, bot_instructions, mod_instructions):
        self._id = _id
        self.name = name
        self.host = host
        self.port = port
        self.hub_uri = hub_uri

        self.conversation_history = ConversationHistory()
        self.teammate = AI_Teammate(name=name, model_name=MODEL, system_instructions=bot_instructions, conversation_history=self.conversation_history)
        self.moderator = AIModerator(model_name=MODEL, system_instructions=mod_instructions, teammate_name=name)
        self.message_queue = asyncio.Queue()

    async def connect(self):
        retries = 0
        while retries < MAX_RETRIES:
            try:
                async with websockets.connect(self.hub_uri, ping_interval=KEEPALIVE_INTERVAL) as websocket:
                    # Register bot with the hub
                    connect_msg = {
                        "type": "ai_connect",
                        "name": self.name,
                        "id": self._id,
                        "origin": "ai",
                        "host": self.host,
                        "port": self.port
                    }
                    await websocket.send(json.dumps(connect_msg))

                    # Start the message processing task
                    asyncio.create_task(self.process_messages(websocket))

                    async for message in websocket:
                        await self.handle_message(message)
            except websockets.exceptions.ConnectionClosedError as e:
                logging.error(f"{self.name} WebSocket connection error: {e}")
                retries += 1
                logging.info(f"{self.name} Retrying connection ({retries}/{MAX_RETRIES})...")
                await asyncio.sleep(5)
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                break

    async def handle_message(self, message_obj_str):
        try:
            message = json.loads(message_obj_str)
            msg_type = message.get("type")

            if msg_type == "msg_recvd":
                sender = message.get("from")
                msg = message.get("message")

                # Maintain chat history
                self.conversation_history.add_message("user", sender, msg)

                if not msg.startswith("[EVENT]"):
                    await self.message_queue.put(message)
        except Exception as e:
            logging.error(f"Error handling message: {e}")

    async def process_messages(self, websocket):
        while True:
            await asyncio.sleep(PROCESSING_INTERVAL)

            # Get the current chat history at this moment
            current_chat_history = self.conversation_history.get_history()

            # Take the last 10 messages for the moderator
            recent_history = self.conversation_history.get_recent_history()

            try:
                if await self.moderator.should_speak_next(recent_history):
                    # If the bot should speak next, use the entire chat history
                    last_message = current_chat_history[-1]["parts"][0]["text"]
                    response = await self.teammate.send_message(message=last_message)
                    response_msg = {
                        "type": "msg_recvd",
                        "from": self._id,
                        "origin": "ai",
                        "message": response
                    }
                    await websocket.send(json.dumps(response_msg))
            except websockets.exceptions.ConnectionClosedError as e:
                logging.error(f"{self.name} WebSocket connection error: {e}")
                await websocket.close()
                break
            except Exception as e:
                logging.error(f"Error processing messages: {e}")

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
        logging.error(f"[!] Instruction file {inst_file} does not exist!")
        exit(-1)
    if not os.path.exists(m_inst_file):
        logging.error(f"[!] Moderator instruction file {m_inst_file} does not exist!")

    with open(inst_file, "r") as f:
        inst = f.read()

    with open(m_inst_file, "r") as f:
        m_inst = f.read()

    bot = Bot(_id=args.id, name=args.name, host=args.host, port=args.port, hub_uri=args.hub_uri, bot_instructions=inst, mod_instructions=m_inst)

    try:
        asyncio.run(bot.connect())
    except KeyboardInterrupt:
        logging.info("Bot process interrupted and stopped.")

if __name__ == "__main__":
    main()

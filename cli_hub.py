import asyncio
import json
import logging
import argparse
from websockets.server import serve

# Configure logging
def configure_logging(console_output):
    handlers = [logging.FileHandler("cli_hub.log")]
    if console_output:
        handlers.append(logging.StreamHandler())
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s: %(message)s',
        handlers=handlers
    )

# Define ANSI color codes for console output
YELLOW = "\033[93m"
RESET = "\033[0m"

# Types documentation ...

class Teammate:
    def __init__(self, _id, name, being, host, port, websocket):
        self._id = _id
        self.name = name
        self.being = being
        self.host = host
        self.port = port
        self.websocket = websocket

    def is_human(self):
        return self.being == "human"
    
    def is_ai(self):
        return self.being == "ai"

TEAMMATES = {}

async def register_teammate(message, websocket):
    name = message.get("name")
    _id = message.get("id")
    being = message.get("being")
    host = message.get("host")
    port = message.get("port")
    tm = Teammate(
        _id=_id,
        name=name,
        being=being,
        host=host,
        port=port,
        websocket=websocket
    )
    TEAMMATES[_id] = tm
    logging.info(f"Registered {_id}: {name} ({being})")

    # Notify everyone that a new teammate has joined
    event_message = {
        "type": "msg_recvd",
        "from": "hub",
        "message": f"[EVENT] {name} has joined the chat."
    }
    await forward_message(websocket, json.dumps(event_message))  # Pass websocket to forward_message

async def unregister_teammate(_id):
    if _id in TEAMMATES:
        name = TEAMMATES[_id].name
        del TEAMMATES[_id]
        logging.info(f"Unregistered {_id}")

        # Notify everyone that a teammate has left
        event_message = {
            "type": "msg_recvd",
            "from": "hub",
            "message": f"[EVENT] {name} has left the chat."
        }
        await forward_message(None, json.dumps(event_message)) # No specific websocket needed for broadcast

async def forward_message(websocket, message):
    for teammate in TEAMMATES.values():
        if teammate.websocket != websocket:  # Compare websockets instead of IDs
            try:
                await teammate.websocket.send(message)
                logging.debug(f"Forwarded message to {teammate.name}")
            except Exception as e:
                logging.error(f"Error forwarding message to {teammate.name}: {e}")

async def echo(websocket, path):
    try:
        logging.info("New connection")
        async for message_obj_str in websocket:
            message = json.loads(message_obj_str)
            msg_type = message.get("type")
            
            if msg_type in ["cli_connect", "ai_connect"]:
                await register_teammate(message, websocket)
            
            elif msg_type in ["cli_disconnect", "ai_disconnect"]:
                _id = message.get("id")
                await unregister_teammate(_id)
            
            elif msg_type == "msg_recvd":
                sender_id = message.get("from")
                msg = message.get("message")
                sender_name = TEAMMATES[sender_id].name if sender_id in TEAMMATES else "Unknown"
                print(f"{YELLOW}{sender_name}{RESET} > {msg}")
                await forward_message(websocket, message_obj_str)  # Pass websocket to forward_message
            
            elif msg_type == "ping":
                await websocket.send(json.dumps({"type": "pong"}))
            
            elif msg_type == "cmd_recvd":
                # Handle commands if necessary
                pass
            
            else:
                logging.warning(f"Unknown websocket message received: {msg_type}")
                logging.warning(message_obj_str)
    except Exception as e:
        logging.error(f"Error in echo: {e}")
    finally:
        # Ensure proper cleanup if the connection is closed
        for _id, teammate in list(TEAMMATES.items()):
            if teammate.websocket == websocket:
                await unregister_teammate(_id)
        logging.info("Connection closed")

async def main(console_output):
    configure_logging(console_output)
    async with serve(echo, "localhost", 9999):
        logging.info("Server started")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CLI Hub")
    parser.add_argument("--console", action="store_true", help="Show logging output to console")
    args = parser.parse_args()

    asyncio.run(main(console_output=args.console))

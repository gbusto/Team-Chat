import asyncio
import json
from websockets.server import serve

"""
Types:
CLI connect: {
    "type": "cli_connect",
    "name": "<name>",
    "id": "<unique identifier>",
    "being": "human",
    "host": "<ip>",
    "port": "<port>",
}

CLI disconnect: {
    "type": "cli_disconnect",
    "id": "<unique identifier>",
}

AI connect: {
    "type": "ai_connect",
    "name": "<name>",
    "id": "<unique identifier>",
    "being": "ai",
    "host": "<ip>",
    "port": "<port>",
}

AI disconnect: {
    "type": "ai_disconnect",
    "id": "<unique identifier>",
}

MSG recvd: {
    "type": "msg_recvd",
    "from": "<unique identifier>",
    "message": "<message>",
}

CMD recvd: {
    "type": "cmd_recvd",
    "from": "<unique identifier>",
    "command": "<command>",
}
"""

class Teammate(object):
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
    print(f"Registered {_id}: {name} ({being})")

async def unregister_teammate(_id):
    if _id in TEAMMATES:
        del TEAMMATES[_id]
        print(f"Unregistered {_id}")

async def forward_message(sender_id, message):
    for _id, teammate in TEAMMATES.items():
        if _id != sender_id:
            await teammate.websocket.send(message)
            print(f"Forwarded message from {_id} to {teammate.name}")

async def echo(websocket, path):
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
            name = TEAMMATES[sender_id]
            msg = message.get("message")
            print(f"{name} > {msg}")
            await forward_message(sender_id, message_obj_str)
        
        elif msg_type == "cmd_recvd":
            # Handle commands if necessary
            pass
        
        else:
            print(f"[?] Unknown websocket message received: {msg_type}")
            print(message_obj_str)

async def main():
    async with serve(echo, "localhost", 9999):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())

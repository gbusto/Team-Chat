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
    def __init__(self, _id, name, being, host, port):
        self._id = _id
        self.name = name
        self.being = being
        self.host = host
        self.port = port

    def is_human(self):
        return self.being == "human"
    
    def is_ai(self):
        return self.being == "ai"
    
TEAMMATES = {}

async def echo(websocket):
    async for message_obj_str in websocket:
        message = json.loads(message_obj_str)
        msg_type = message.get("type")
        
        if msg_type == "cli_connect":
            # A human teammate has connected
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
                port=port
            )
            TEAMMATES[_id] = tm

        elif msg_type == "ai_connect":
            # An AI teammate has connected
            name = message.get("name")
            _id = message.get("id")
            being = message.get("being")
            tm = Teammate(
                _id=_id,
                name=name,
                being=being,
                host=host,
                port=port
            )
            TEAMMATES[_id] = tm

        elif msg_type == "msg_recvd":
            # Received a message from someone
            sender = message.get("from")
            msg = message.get("message")

            for tm in TEAMMATES:
                if tm != sender:
                    
        
        elif msg_type == "cmd_recvd":
            # Received a command from someone
            pass

        else:
            print("[?] Unknown websocket message received: {}".format(msg_type))
            print(message_obj_str)
            
        await websocket.send(message)

async def main():
    async with serve(echo, "localhost", 9999):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
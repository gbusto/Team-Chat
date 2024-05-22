import os
import asyncio
import json
import websockets
import argparse

class CLIClient:
    def __init__(self, _id, name, host, port, hub_uri):
        self._id = _id
        self.name = name
        self.host = host
        self.port = port
        self.hub_uri = hub_uri

    async def connect(self):
        async with websockets.connect(self.hub_uri) as websocket:
            # Register client with the hub
            connect_msg = {
                "type": "cli_connect",
                "name": self.name,
                "id": self._id,
                "being": "human",
                "host": self.host,
                "port": self.port
            }
            await websocket.send(json.dumps(connect_msg))

            receive_task = asyncio.create_task(self.receive_messages(websocket))
            send_task = asyncio.create_task(self.send_messages(websocket))

            await asyncio.wait([receive_task, send_task], return_when=asyncio.FIRST_COMPLETED)

    async def receive_messages(self, websocket):
        async for message in websocket:
            msg = json.loads(message)
            print(f"{msg.get('from')}: {msg.get('message')}")

    async def send_messages(self, websocket):
        while True:
            msg = input(f"{self.name} > ")
            message_obj = {
                "type": "msg_recvd",
                "from": self._id,
                "message": msg
            }
            await websocket.send(json.dumps(message_obj))

def main():
    parser = argparse.ArgumentParser(description="CLI Client")
    parser.add_argument("--id", type=str, required=True, help="Unique identifier for the client")
    parser.add_argument("--name", type=str, required=True, help="Name of the client")
    parser.add_argument("--host", type=str, required=True, help="Host IP address")
    parser.add_argument("--port", type=int, required=True, help="Port number")
    parser.add_argument("--hub_uri", type=str, required=True, help="WebSocket URI of the hub")

    args = parser.parse_args()

    client = CLIClient(_id=args.id, name=args.name, host=args.host, port=args.port, hub_uri=args.hub_uri)

    asyncio.run(client.connect())

if __name__ == "__main__":
    main()

import os
import asyncio
import json
import websockets
import argparse
import logging

MAX_RETRIES = 5  # Maximum number of retries for WebSocket connection
KEEPALIVE_INTERVAL = 300  # Increase keepalive interval
TIMEOUT = 20  # WebSocket timeout

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler("cli_client.log"),
        logging.StreamHandler()
    ]
)

class CLIClient:
    def __init__(self, _id, name, host, port, hub_uri):
        self._id = _id
        self.name = name
        self.host = host
        self.port = port
        self.hub_uri = hub_uri

    async def connect(self):
        retries = 0
        while retries < MAX_RETRIES:
            try:
                logging.info(f"Connecting to {self.hub_uri}")
                async with websockets.connect(self.hub_uri, ping_interval=KEEPALIVE_INTERVAL, timeout=TIMEOUT) as websocket:
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
                    logging.info(f"Connected to {self.hub_uri} as {self.name}")

                    receive_task = asyncio.create_task(self.receive_messages(websocket))
                    send_task = asyncio.create_task(self.send_messages(websocket))

                    done, pending = await asyncio.wait(
                        [receive_task, send_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    for task in pending:
                        task.cancel()

                    for task in done:
                        if task.exception():
                            raise task.exception()
                    break  # Exit the loop if tasks complete successfully
            except websockets.exceptions.ConnectionClosedError as e:
                logging.error(f"WebSocket connection closed unexpectedly: {e}")
                retries += 1
                logging.info(f"Retrying connection ({retries}/{MAX_RETRIES})...")
                await asyncio.sleep(5)
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                break

    async def receive_messages(self, websocket):
        try:
            async for message in websocket:
                msg = json.loads(message)
                logging.info(f"Received message from {msg.get('from')}: {msg.get('message')}")
                print(f"{msg.get('from')}: {msg.get('message')}")
        except websockets.exceptions.ConnectionClosedError as e:
            logging.error(f"Receive connection closed error: {e}")
        except Exception as e:
            logging.error(f"Error receiving message: {e}")

    async def send_messages(self, websocket):
        try:
            while True:
                msg = input(f"{self.name} > ")
                message_obj = {
                    "type": "msg_recvd",
                    "from": self._id,
                    "message": msg
                }
                await websocket.send(json.dumps(message_obj))
                logging.info(f"Sent message: {msg}")
        except websockets.exceptions.ConnectionClosedError as e:
            logging.error(f"Send connection closed error: {e}")
        except Exception as e:
            logging.error(f"Error sending message: {e}")

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

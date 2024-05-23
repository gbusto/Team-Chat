import os
import asyncio
import json
import websockets
import argparse
import logging
import time
import aioconsole

MAX_RETRIES = 5  # Maximum number of retries for WebSocket connection
INITIAL_RETRY_DELAY = 1  # Initial delay before retrying connection
MAX_RETRY_DELAY = 60  # Maximum delay before retrying connection
KEEPALIVE_INTERVAL = 300  # Keepalive interval
TIMEOUT = 20  # WebSocket timeout

# Configure logging
def configure_logging(console_output=False):
    """Configures logging to file and optionally to console."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s: %(message)s',
        filename="cli_client.log",
        filemode='a'
    )

    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)  # Set console log level
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)

class CLIClient:
    def __init__(self, _id, name, host, port, hub_uri):
        self._id = _id
        self.name = name
        self.host = host
        self.port = port
        self.hub_uri = hub_uri
        self.websocket = None

    async def connect(self):
        retries = 0
        delay = INITIAL_RETRY_DELAY

        while retries < MAX_RETRIES:
            try:
                logging.info(f"Connecting to {self.hub_uri}")
                self.websocket = await websockets.connect(self.hub_uri, ping_interval=KEEPALIVE_INTERVAL, timeout=TIMEOUT)

                # Register client with the hub
                connect_msg = {
                    "type": "cli_connect",
                    "name": self.name,
                    "id": self._id,
                    "origin": "human",
                    "host": self.host,
                    "port": self.port
                }
                await self.websocket.send(json.dumps(connect_msg))
                logging.info(f"Connected to {self.hub_uri} as {self.name}")

                # Start tasks concurrently
                receive_task = asyncio.create_task(self.receive_messages())
                send_task = asyncio.create_task(self.send_messages())

                # Ensure keep_alive is always running
                keepalive_task = asyncio.create_task(self.keep_alive())
                await keepalive_task

            except websockets.exceptions.ConnectionClosed as e:
                logging.error(f"WebSocket connection closed: {e}")
                retries += 1
                logging.info(f"Retrying connection in {delay} seconds ({retries}/{MAX_RETRIES})...")
                await asyncio.sleep(delay)
                delay = min(MAX_RETRY_DELAY, delay * 2)

            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                break

    async def receive_messages(self):
        try:
            async for message in self.websocket:
                msg = json.loads(message)
                logging.info(f"Received message from {msg.get('from')}: {msg.get('message')}")
                print(f"{msg.get('from')}: {msg.get('message')}")
        except websockets.exceptions.ConnectionClosed:
            logging.error("Receive connection closed unexpectedly.")
            # Optionally: attempt to reconnect here

    async def send_messages(self):
        try:
            while True:
                msg = await aioconsole.ainput(f"{self.name} > ")  # Asynchronous input
                message_obj = {
                    "type": "msg_recvd",
                    "from": self._id,
                    "origin": "human",
                    "message": msg
                }
                await self.websocket.send(json.dumps(message_obj))
                logging.info(f"Sent message: {msg}")
        except websockets.exceptions.ConnectionClosed:
            logging.error("Send connection closed unexpectedly.")
            # Optionally: attempt to reconnect here

    async def keep_alive(self):
        while True:
            try:
                await self.websocket.ping()
                logging.debug("Sent ping to keep connection alive")
                await asyncio.sleep(KEEPALIVE_INTERVAL)
            except websockets.exceptions.ConnectionClosed:
                logging.error("Keep-alive connection closed unexpectedly.")
                break

def main():
    parser = argparse.ArgumentParser(description="CLI Client")
    parser.add_argument("--id", type=str, required=True, help="Unique identifier for the client")
    parser.add_argument("--name", type=str, required=True, help="Name of the client")
    parser.add_argument("--host", type=str, required=True, help="Host IP address")
    parser.add_argument("--port", type=int, required=True, help="Port number")
    parser.add_argument("--hub_uri", type=str, required=True, help="WebSocket URI of the hub")
    parser.add_argument("--console", action="store_true", help="Enable console logging")  # Add console argument

    args = parser.parse_args()

    configure_logging(console_output=args.console)  # Configure logging based on argument

    client = CLIClient(_id=args.id, name=args.name, host=args.host, port=args.port, hub_uri=args.hub_uri)
    asyncio.run(client.connect())

if __name__ == "__main__":
    main()

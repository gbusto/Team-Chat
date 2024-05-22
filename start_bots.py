import os
import json
import subprocess
import signal
import time

def load_bot_configs(directory):
    bot_configs = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            with open(os.path.join(directory, filename), 'r') as file:
                bot_configs.append(json.load(file))
    return bot_configs

def start_bot(config):
    cmd = [
        "python", "bot.py",
        "--id", config["id"],
        "--name", config["name"],
        "--host", config["host"],
        "--port", str(config["port"]),
        "--hub_uri", config["hub_uri"],
        "--instruction-file", config["instruction_file"],
        "--moderator-instruction-file", config["moderator_instruction_file"]
    ]
    return subprocess.Popen(cmd)

def main():
    bot_configs = load_bot_configs("bots")
    processes = []

    try:
        for config in bot_configs:
            if "id" in config:  # It's a bot config
                process = start_bot(config)
                processes.append(process)
        
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping all bots...")
        for process in processes:
            process.send_signal(signal.SIGINT)
            process.wait()
        print("All bots stopped.")

if __name__ == "__main__":
    main()

import os
import json
import subprocess
import signal
import time
import argparse

def load_bot_configs(directory, bot_names):
    bot_configs = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            with open(os.path.join(directory, filename), 'r') as file:
                config = json.load(file)
                if bot_names == "*" or config.get("name") in bot_names:
                    bot_configs.append(config)
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
        "--moderator-instruction-file", config["moderator_instruction_file"],
        "--teammate-extra-params", json.dumps(config["teammate_extra_params"]),
        "--mod-extra-params", json.dumps(config["mod_extra_params"]),
        "--llm", config["llm"]
    ]
    return subprocess.Popen(cmd)

def main():
    parser = argparse.ArgumentParser(description="Start AI Bots")
    parser.add_argument("--bots", type=str, default="*", help="Comma-delimited list of bot names to load (default: all bots)")
    args = parser.parse_args()

    bot_names = args.bots.split(",") if args.bots != "*" else "*"
    bot_configs = load_bot_configs("bots", bot_names)
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

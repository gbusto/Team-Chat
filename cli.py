import sys
from team_logic import manage_conversation, Conversation

class CLIComms(object):
    def __init__(self):
        pass

    def send(self, response_obj):
        # ANSI escape codes for colors
        COLORS = {
            "Alex": "\033[94m",  # Blue
            "Jordan": "\033[92m",  # Green
            "Casey": "\033[93m",  # Yellow
            "Riley": "\033[91m",  # Red
            "Morgan": "\033[95m",  # Magenta
            "Gabe": "\033[96m"  # Cyan
        }
        RESET_COLOR = "\033[0m"

        # Send output back to the user
        name = response_obj.get("name")
        message = response_obj.get("message")
        color = COLORS.get(name, "\033[97m")  # Default to white if name not found

        # print("=" * 100)
        print(f"{color}{name} > {message}{RESET_COLOR}")
        # print("=" * 100)

    def recv(self):
        # Receive input from the user
        response = input("user > ")
        if response in ["q", "quit", "exit"]:
            print("[+] User requested to end conversation")
            sys.exit(0)
        return response

if __name__ == "__main__":
    comms = CLIComms()
    conversation = Conversation(username="Gabe", comms=comms)
    response = input("user > ")
    conversation.start_conversation(response)
    
    # manage_conversation(CLIComms(), debug=True)

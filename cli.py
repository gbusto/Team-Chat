import sys
from team_logic import manage_conversation
class CLIComms(object):
    def __init__(self):
        pass

    def send(self, response_obj):
        # Send output back to the user
        name = response_obj.get("name")
        message = response_obj.get("message")
        print("="*100)
        print("{} > {}".format(name, message))
        print("="*100)

    def recv(self):
        # Receive input from the user
        response = input("user > ")
        if response in ["q", "quit", "exit"]:
            print("[+] User requested to end conversation")
            sys.exit(0)
        return response
    
if __name__ == "__main__":
    manage_conversation(CLIComms(), debug=True)
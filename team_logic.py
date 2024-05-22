import os
import time
import google.generativeai as genai
from instructions import *

genai.configure(api_key=os.environ['GOOGLE_DEV_API_KEY'])

MODEL = "gemini-1.5-flash-latest"
# Delay in seconds; we need to delay it because Google hasn't given us billing access yet for the API so we're stuck on the FREE plan with the free plan restrictions
DELAY = 5

class SharedChatHistory:
    def __init__(self):
        self.history = []

    def add_message(self, role, name, text):
        self.history.append({"role": role, "name": name, "text": text})

    def get_history(self):
        return self.history

    def format_history(self):
        formatted_history = []
        for entry in self.history:
            formatted_history.append(f"{entry['name']} ({entry['role']}): {entry['text']}")
        return "\n".join(formatted_history)


class AI_Teammate:
    def __init__(self, name, model_name, system_instructions, shared_history):
        self.name = name
        self.model = genai.GenerativeModel(model_name, system_instruction=system_instructions)
        self.shared_history = shared_history

    def send_message(self, message, history=[]):
        time.sleep(DELAY)

        self.chat = self.model.start_chat(history=history)
        self.shared_history.add_message("user", self.name, message)
        response = self.chat.send_message(message)
        reply = response.text
        self.shared_history.add_message("model", self.name, reply)
        return reply
    
    def get_history(self):
        return self.chat.history


class AIModerator:
    def __init__(self, model_name, system_instructions):
        self.model = genai.GenerativeModel(model_name, system_instruction=system_instructions)
        self.chat = self.model.start_chat()

    def determine_next_speaker(self, chat_history):
        time.sleep(DELAY)

        history_text = "\n".join([f"{entry['name']} ({entry['role']}): {entry['text']}" for entry in chat_history])
        prompt = f"Based on the following conversation, who should speak next?\n\n{history_text}\n\nRespond with ONLY the next speaker's name, e.g., \"Aristotle\""
        response = self.chat.send_message(prompt)
        next_speaker = response.text.strip()
        # print(f"DEBUG: Moderator response: {next_speaker}")  # Add debug information
        return next_speaker
    
def dbg(prepend="[-]", message="", debug=False):
    if debug:
        print("{} {}".format(prepend, message))
    else:
        pass

class Conversation(object):
    def __init__(self, username, comms):
        self.username = username
        self.comms = comms

        # The history object that Google updates and manages for us
        self.history = []
        # Our own shared history... I'm keeping it around because we may need it later
        self.shared_history = SharedChatHistory()

        self.teammates = {
            'Alex': AI_Teammate(
                name='Alex',
                model_name=MODEL,
                system_instructions=alex_system_instructions,
                shared_history=self.shared_history),
            'Jordan': AI_Teammate(
                name='Jordan',
                model_name=MODEL,
                system_instructions=jordan_system_instructions,
                shared_history=self.shared_history),
            'Casey': AI_Teammate(
                name='Casey',
                model_name=MODEL,
                system_instructions=casey_system_instructions,
                shared_history=self.shared_history),
            'Riley': AI_Teammate(
                name='Riley',
                model_name=MODEL,
                system_instructions=riley_system_instructions,
                shared_history=self.shared_history),
            'Morgan': AI_Teammate(
                name='Morgan',
                model_name=MODEL,
                system_instructions=morgan_system_instructions,
                shared_history=self.shared_history),
        }

        self.moderator = AIModerator(MODEL, system_instructions=moderator_system_instructions)

    def start_conversation(self, start_message):
        response = start_message
        self.shared_history.add_message("user", self.username, response)

        while True:
            next_speaker_name = self.moderator.determine_next_speaker(self.shared_history.get_history())
            dbg("[+++]", "Passing conversation over to {}".format(next_speaker_name), debug=True)

            if next_speaker_name != "Gabe":
                next_speaker = self.teammates[next_speaker_name]

                response = next_speaker.send_message(
                    message=response,
                    history=self.history
                )
                self.history = next_speaker.get_history()

                response_obj = {
                    "role": "assistant",
                    "name": next_speaker_name,
                    "message": response
                }
                self.comms.send(response_obj)
            else:
                user_input = self.comms.recv()
                if user_input.strip():
                    # If the user sent any kind of message, add it to the chat
                    response = "[{}]: {}".format(self.username, user_input)
                    self.shared_history.add_message("user", self.username, response)


# TODO: Remove this code! Keeping it as reference for now
def manage_conversation(comms, debug=False):
    # User starts the conversation
    USERNAME = "Gabe"
    current_speaker = USERNAME

    # Shared chat history instance
    shared_history = SharedChatHistory()

    # Moderator instance
    moderator = AIModerator(MODEL, system_instructions=moderator_system_instructions)
    
    teammates = {
        'Alex': AI_Teammate(name='Alex', model_name=MODEL, system_instructions=alex_system_instructions, shared_history=shared_history),
        'Jordan': AI_Teammate(name='Jordan', model_name=MODEL, system_instructions=jordan_system_instructions, shared_history=shared_history),
        'Casey': AI_Teammate(name='Casey', model_name=MODEL, system_instructions=casey_system_instructions, shared_history=shared_history),
        'Riley': AI_Teammate(name='Riley', model_name=MODEL, system_instructions=riley_system_instructions, shared_history=shared_history),
        'Morgan': AI_Teammate(name='Morgan', model_name=MODEL, system_instructions=morgan_system_instructions, shared_history=shared_history),
    }

    history = []
    response = comms.recv()
    shared_history.add_message("user", current_speaker, response)

    while True:
        next_speaker_name = moderator.determine_next_speaker(shared_history.get_history())
        dbg("[+++]", "Passing conversation over to {}".format(next_speaker_name), debug=debug)

        if next_speaker_name != "Gabe":
            next_speaker = teammates[next_speaker_name]

            response = next_speaker.send_message(
                message=response,
                history=history
            )
            history = next_speaker.get_history()

            response_obj = {
                "role": "assistant",
                "name": next_speaker_name,
                "message": response
            }
            comms.send(response_obj)
        else:
            user_input = comms.recv()
            if user_input.strip():
                if user_input == "get_history":
                    last_speaker = next_speaker
                    history = last_speaker.chat.history
                    print(history)
                else:
                    # If the user sent any kind of message, add it to the chat
                    response = "[{}]: {}".format(USERNAME, user_input)
                    shared_history.add_message("user", USERNAME, response)
            else:
                # If the user just pressed enter or sent a blank message, they didn't want to interrupt
                current_speaker = next_speaker_name
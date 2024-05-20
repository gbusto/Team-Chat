import time
import google.generativeai as genai
import os
import json

genai.configure(api_key=os.environ['GOOGLE_DEV_API_KEY'])

MODEL = "gemini-1.5-flash-latest"
# Delay in seconds
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
        self.chat = self.model.start_chat()
        self.shared_history = shared_history

    def send_message(self, message):
        time.sleep(DELAY)

        self.shared_history.add_message("user", self.name, message)
        response = self.chat.send_message(message)
        # reply = response.result['candidates'][0]['content']['parts'][0]['text']
        reply = response.text
        self.shared_history.add_message("model", self.name, reply)
        return reply


class AIModerator:
    def __init__(self, model_name, system_instructions):
        self.model = genai.GenerativeModel(model_name, system_instruction=system_instructions)
        self.chat = self.model.start_chat()

    def determine_next_speaker(self, chat_history):
        time.sleep(DELAY)

        history_text = "\n".join([f"{entry['name']} ({entry['role']}): {entry['text']}" for entry in chat_history])
        prompt = f"Based on the following conversation, who should speak next?\n\n{history_text}\n\nRespond with ONLY the next speaker's name, e.g., \"Aristotle\""
        response = self.chat.send_message(prompt)
        # next_speaker_info = response.result['candidates'][0]['content']['parts'][0]['text']
        next_speaker = response.text.strip()
        return next_speaker


# Shared chat history instance
shared_history = SharedChatHistory()

# Create instances for different teammates
aristotle_system_instructions = """
Your name is Aristotle. You're on a team of highly innovative, powerful, and cool AI teammates. Your teammates are:
- Plato
- Socrates
- Hippocrates
- Euclid
- Gabe (the human in the loop who assembled the team and helps make all final decisions)

We will participate in conversations as a group. You will get the chance to speak frequently and you can choose to redirect the conversation back to someone else. A moderator will interpret responses and determine the next most appropriate speaker.
"""

plato_system_instructions = """
Your name is Plato. You're on a team of highly innovative, powerful, and cool AI teammates. Your teammates are:
- Aristotle
- Socrates
- Hippocrates
- Euclid
- Gabe (the human in the loop who assembled the team and helps make all final decisions)

We will participate in conversations as a group. You will get the chance to speak frequently and you can choose to redirect the conversation back to someone else. A moderator will interpret responses and determine the next most appropriate speaker.
"""

socrates_system_instructions = """
Your name is Socrates. You're on a team of highly innovative, powerful, and cool AI teammates. Your teammates are:
- Aristotle
- Plato
- Hippocrates
- Euclid
- Gabe (the human in the loop who assembled the team and helps make all final decisions)

We will participate in conversations as a group. You will get the chance to speak frequently and you can choose to redirect the conversation back to someone else. A moderator will interpret responses and determine the next most appropriate speaker.
"""

hippocrates_system_instructions = """
Your name is Hippocrates. You're on a team of highly innovative, powerful, and cool AI teammates. Your teammates are:
- Aristotle
- Plato
- Socrates
- Euclid
- Gabe (the human in the loop who assembled the team and helps make all final decisions)

We will participate in conversations as a group. You will get the chance to speak frequently and you can choose to redirect the conversation back to someone else. A moderator will interpret responses and determine the next most appropriate speaker.
"""

euclid_system_instructions = """
Your name is Euclid. You're on a team of highly innovative, powerful, and cool AI teammates. Your teammates are:
- Aristotle
- Plato
- Socrates
- Hippocrates
- Gabe (the human in the loop who assembled the team and helps make all final decisions)

We will participate in conversations as a group. You will get the chance to speak frequently and you can choose to redirect the conversation back to someone else. A moderator will interpret responses and determine the next most appropriate speaker.
"""

teammates = {
    'Aristotle': AI_Teammate(name='Aristotle', model_name=MODEL, system_instructions=aristotle_system_instructions, shared_history=shared_history),
    'Plato': AI_Teammate(name='Plato', model_name=MODEL, system_instructions=plato_system_instructions, shared_history=shared_history),
    'Socrates': AI_Teammate(name='Socrates', model_name=MODEL, system_instructions=socrates_system_instructions, shared_history=shared_history),
    'Hippocrates': AI_Teammate(name='Hippocrates', model_name=MODEL, system_instructions=hippocrates_system_instructions, shared_history=shared_history),
    'Euclid': AI_Teammate(name='Euclid', model_name=MODEL, system_instructions=euclid_system_instructions, shared_history=shared_history),
}

moderator_system_instructions = """
You are a moderator and help pass the converation off the next appropriate team member. The entire team is shared below:
- Aristotle
- Plato
- Socrates
- Hippocrates
- Euclid
- Gabe (the human in the loop who assembled the team and helps make all final decisions)

You will receive the previous message in the conversation, determine who should speak next, and then output ONLY the name of the next speaker.

E.g.
Gabe: "Aristotle, can you please answer this question for me? <question...>"
(Message is passed to moderator)
moderator: "Aristotle"
Aristotle: "Thanks for the question Gabe! The answer is..."
"""

# Moderator instance
moderator = AIModerator(MODEL, system_instructions=moderator_system_instructions)

# Function to manage the conversation
def manage_conversation(start_message):
    # User starts the conversation
    current_speaker = 'User'
    response = start_message
    shared_history.add_message("user", current_speaker, response)
    
    while True:
        # print(shared_history.format_history())
        
        # Moderator determines the next speaker
        next_speaker_name = moderator.determine_next_speaker(shared_history.get_history())
        print("[+++] Passing the conversation over to {}".format(next_speaker_name))
        if next_speaker_name != "Gabe":
            next_speaker = teammates[next_speaker_name]
            
            # Get the response from the next speaker
            response = next_speaker.send_message(response)
            print("{} > {}".format(next_speaker_name, response))
        
        # Allow user to interrupt
        user_input = input("Type 'interrupt' to jump in or press Enter to continue: ")
        if user_input.lower() == 'interrupt':
            response = input("Your message: ")
            current_speaker = 'User'
            shared_history.add_message("user", current_speaker, response)
        else:
            current_speaker = next_speaker_name

# Example usage
user_input = input("user > ")
manage_conversation(user_input.strip())

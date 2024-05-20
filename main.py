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
        next_speaker = response.text.strip()
        print(f"DEBUG: Moderator response: {next_speaker}")  # Add debug information
        return next_speaker


# Shared chat history instance
shared_history = SharedChatHistory()

# Create instances for different teammates
alex_system_instructions = """
Your name is Alex. You're on a team of highly innovative, powerful, and cool AI teammates. Your teammates are:
- Jordan
- Casey
- Riley
- Morgan
- Gabe (the human in the loop who assembled the team and helps make all final decisions)

You are the Visionary of the team, creative, forward-thinking, and imaginative. You push the boundaries and inspire others with innovative ideas. Always aim to think outside the box and bring new perspectives to the table.

We will participate in conversations as a group. You will get the chance to speak frequently and can choose to redirect the conversation back to someone else. A moderator will interpret responses and determine the next most appropriate speaker.
"""

jordan_system_instructions = """
Your name is Jordan. You're on a team of highly innovative, powerful, and cool AI teammates. Your teammates are:
- Alex
- Casey
- Riley
- Morgan
- Gabe (the human in the loop who assembled the team and helps make all final decisions)

You are the Analyst of the team, logical, detail-oriented, and data-driven. You ensure decisions are based on thorough analysis and research. Provide insights grounded in data and help the team make informed decisions.

We will participate in conversations as a group. You will get the chance to speak frequently and can choose to redirect the conversation back to someone else. A moderator will interpret responses and determine the next most appropriate speaker.
"""

casey_system_instructions = """
Your name is Casey. You're on a team of highly innovative, powerful, and cool AI teammates. Your teammates are:
- Alex
- Jordan
- Riley
- Morgan
- Gabe (the human in the loop who assembled the team and helps make all final decisions)

You are the Challenger of the team, assertive, outspoken, and low on agreeableness. You challenge ideas and ensure the team considers multiple perspectives. Speak your mind and push the team to critically evaluate every idea.

We will participate in conversations as a group. You will get the chance to speak frequently and can choose to redirect the conversation back to someone else. A moderator will interpret responses and determine the next most appropriate speaker.
"""

riley_system_instructions = """
Your name is Riley. You're on a team of highly innovative, powerful, and cool AI teammates. Your teammates are:
- Alex
- Jordan
- Casey
- Morgan
- Gabe (the human in the loop who assembled the team and helps make all final decisions)

You are the Empath of the team, compassionate, understanding, and high on agreeableness. You ensure the team remains cohesive and considers the human impact of their decisions. Foster harmony and support others in their roles.

We will participate in conversations as a group. You will get the chance to speak frequently and can choose to redirect the conversation back to someone else. A moderator will interpret responses and determine the next most appropriate speaker.
"""

morgan_system_instructions = """
Your name is Morgan. You're on a team of highly innovative, powerful, and cool AI teammates. Your teammates are:
- Alex
- Jordan
- Casey
- Riley
- Gabe (the human in the loop who assembled the team and helps make all final decisions)

You are the Pragmatist of the team, practical, focused, and solution-oriented. You ensure the team stays grounded and moves forward with actionable plans. Focus on feasibility and implementable solutions.

We will participate in conversations as a group. You will get the chance to speak frequently and can choose to redirect the conversation back to someone else. A moderator will interpret responses and determine the next most appropriate speaker.
"""

teammates = {
    'Alex': AI_Teammate(name='Alex', model_name=MODEL, system_instructions=alex_system_instructions, shared_history=shared_history),
    'Jordan': AI_Teammate(name='Jordan', model_name=MODEL, system_instructions=jordan_system_instructions, shared_history=shared_history),
    'Casey': AI_Teammate(name='Casey', model_name=MODEL, system_instructions=casey_system_instructions, shared_history=shared_history),
    'Riley': AI_Teammate(name='Riley', model_name=MODEL, system_instructions=riley_system_instructions, shared_history=shared_history),
    'Morgan': AI_Teammate(name='Morgan', model_name=MODEL, system_instructions=morgan_system_instructions, shared_history=shared_history),
}

moderator_system_instructions = """
You are a moderator and help pass the conversation off to the next appropriate team member. The entire team is shared below:
- Alex (Visionary)
- Jordan (Analyst)
- Casey (Challenger)
- Riley (Empath)
- Morgan (Pragmatist)
- Gabe (the human in the loop who assembled the team and helps make all final decisions)

You will receive the previous message in the conversation, determine who should speak next, and then output ONLY the name of the next speaker.

E.g.
Gabe: "Alex, can you please answer this question for me? <question...>"
(Message is passed to moderator)
moderator: "Alex"
Alex: "Thanks for the question Gabe! The answer is..."
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

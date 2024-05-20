import google.generativeai as genai
import os

genai.configure(api_key=os.environ['GOOGLE_DEV_API_KEY'])

model = genai.GenerativeModel('gemini-pro')
chat = model.start_chat()

user_input = input("user > ")
while user_input not in ["q", "quit", "exit"]:
    response = chat.send_message(user_input.strip())
    print("assistant > {}".format(response.text))

    import pdb
    pdb.set_trace()
    
    user_input = input("user > ")

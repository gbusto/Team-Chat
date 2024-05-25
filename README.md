# AI Team Collaboration Chat

This project is a distributed chat application that allows for communication between human users and multiple AI teammates. It uses a WebSocket server (CLI hub) to manage connections and message forwarding, a React-based frontend for the chat interface, and Python scripts to manage AI teammates and their interactions.

We're using Google's Gemini Flash model and API for now because 1) it seems easier to build with their API than OpenAI's, 2) they have a decent free plan and competing model to GPT-4o (called Gemini Flash 1.5), and finally because 3) OpenAI [Context Tokens](https://gboostlabs.com/blogs/dev-blog/openai-assistants-api-and-context-tokens) are a huge billing issue and I need a better way to manage conversation history and context to avoid a massive bill.

Eventually I'll create an OpenAI teammate file, and I'll also do the same for Claude. And maybe even one for Llama 3. That's the goal.

## Updates
### **May 24 2024**
I've added support for OpenAI models now and ran the first test today (May 24 2024] where GPT-4o talked with Gemini Flash. Super cool.

In order to use it though, you need to create a new Assistant in the OpenAI interface and then use that Assistant ID in the JSON file for an OpenAI bot. See `bots/jasper.json` for an example. It's not the best implementation, but it works well enough for now.

## Features
-   Real-time chat with AI and human teammates
-   Support for Markdown formatting and code syntax highlighting in chat messages
-   Conversation history saved locally on the server
-   Distributed architecture allowing asynchronous responses from AI teammates

## Requirements
-   Python 3.x
-   Node.js and npm
-   Google API key (for Google Gemini API)
-   OpenAI API key if you want to run those models

## Setup

### 1. Install Python Dependencies
```
pip install -r requirements.txt
```

### 2. Install npm Dependencies

Navigate to the `chat-app/` directory and install the npm dependencies.
```
cd chat-app/
npm install
```

### 3. Google API Key

Obtain a Google API key to use the Google Gemini API. Note that there is a delay in the code due to usage quotas on the free plan.

## Running the Application

### 1. Start the WebSocket Server (CLI Hub)

Start the WebSocket server that manages connections and message forwarding.
```
python cli_hub.py --console
```

Running with the `--console` flag will show logging output in the console. Without this flag, logs will be written to a log file.

### 2. Start the React App

Navigate to the `chat-app/` directory and start the React app.
```
cd chat-app/
npm start
```

### 3. Start the AI Bots

Run the script to start the AI bots.
```
python start_bots.py
```

## Using the Application

-   **Connect to the Chat**: Open the React app in your browser. Enter a unique ID (can be your name) and a name (doesn't have to be unique) to connect to the chat.
-   **Chat Interface**: You will arrive at the chat window where you can communicate with other users and AI teammates.

## Application Flow and How It Works

1.  **WebSocket Server (CLI Hub)**:
    -   Manages connections from clients (human users and AI teammates).
    -   Forwards messages to all connected clients except the sender.
    -   Saves conversation history locally in `.chat` files with a human-readable timestamp.
2.  **React Chat App**:
    -   Provides a chat interface for human users.
    -   Displays messages with Markdown formatting and syntax highlighting for code blocks.
3.  **AI Bots**:
    -   Managed by a Python script (`start_bots.py`).
    -   Each bot can respond asynchronously to messages.
    -   Includes an AI moderator to manage conversation flow and ensure relevance.

## Interesting Insights and Learnings
-   **AI Moderation**: An AI moderator can help keep the conversation on track and manage clutter. It sometimes gets confused, but I'm testing ways to improve its function.
-   **AI Agents for Specific Tasks**: An AI agent can be set up to communicate on behalf of a user with additional context. As humans, we need to type. And even with the long delay that's in place now, these AI teammates can easily overwhelm the chat with ideas, questions, and text. So I wanted to try creating an AI agent to speak on my behalf to keep conversation moving faster, with the understanding that it should ask me for something if it doesn't know the answer. See bot instructions I have now in the `instructions/` directory.
-   **Distributed Responses**: AI teammates can respond asynchronously, allowing for faster iteration on ideas. I think this is super cool and interesting. It also allows us to build AI teammates using OpenAI's API, Claude's API, and maybe even other open source models to have a diverse group of skills and training involved in coming up with solutions.
-   **Handling AI Hallucinations**: AI teammates can sometimes forget their names or invent non-existent teammates. Reminding them of their identity and team members before prompting might be able to mitigate this, but I need to test that out. The hallucinations are really strong in this group and I can't help but laugh sometimes 😂 
-   **Balancing AI Team Sizes**: Starting with 5 AI teammates can be overwhelming. Reducing the number to 3 plus a moderator and an agent for the user improves performance and coherence.

## Future Improvements
-   **Load Chat History**: Implement a mechanism to load previous chat histories.
-   **Reduce Need for Moderators**: AI moderators help, but it's an extra API call needed to help a teammate know whether or not they should respond. On the free plan, this really limits how much you can use this. And it will increase usage costs on a pay-as-you-go plan.
-   **Reduce Hallucinations**: ***update - I updated the moderator prompt to include a reminder of their names and it seems to have made a positive impact.*** Improve the reliability of AI teammates by refining their prompts and context reminders.
-   **Enhanced Moderation**: Further develop the AI moderator to handle more complex conversation flows and maintain engagement.
-   **Enhanced AI Agent**: Improve its ability to speak on your behalf and learn when to ask for help. Once you remove the limitation of the long delay because we're on the free plan, these conversations will FLY. And it'll be useful to have a teammate with context about something you want to discuss to interact at speed with the team.
-   **So many more!** There are so many other things I want to add: better ability to task the group, give them ability to write code, search the web, or do more agent interactions with apps; queue up questions for you while you're offline so they can work around the clock; provide summaries; and more.

## Contributing
Contributions are welcome! Please fork the repository and create a pull request with your changes.
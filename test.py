import unittest
from unittest.mock import Mock
from main import SharedChatHistory, AI_Teammate, AIModerator

class TestSharedChatHistory(unittest.TestCase):
    def setUp(self):
        self.history = SharedChatHistory()

    def test_add_message(self):
        # Test adding a message to the chat history
        self.history.add_message("user", "John", "Hello")
        self.assertEqual(len(self.history.history), 1)
        self.assertEqual(self.history.history[0], {"role": "user", "name": "John", "text": "Hello"})

    def test_get_history(self):
        # Test retrieving the chat history
        self.history.add_message("user", "John", "Hello")
        self.history.add_message("model", "AI", "Hi there!")
        self.assertEqual(len(self.history.get_history()), 2)

    def test_format_history(self):
        # Test formatting the chat history
        self.history.add_message("user", "John", "Hello")
        self.history.add_message("model", "AI", "Hi there!")
        expected_output = "John (user): Hello\nAI (model): Hi there!"
        self.assertEqual(self.history.format_history(), expected_output)

class TestAITeammate(unittest.TestCase):
    def setUp(self):
        self.shared_history = SharedChatHistory()
        self.teammate = AI_Teammate("Alex", "model_name", "system_instructions", self.shared_history)

    def test_send_message(self):
        # Test sending a message as an AI teammate
        # Mock the chat.send_message() method to return a predefined response
        self.teammate.chat.send_message = lambda message: Mock(text="Mocked response")

        response = self.teammate.send_message("Hello")
        self.assertEqual(response, "Mocked response")
        self.assertEqual(len(self.shared_history.history), 2)
        self.assertEqual(self.shared_history.history[0], {"role": "user", "name": "Alex", "text": "Hello"})
        self.assertEqual(self.shared_history.history[1], {"role": "model", "name": "Alex", "text": "Mocked response"})

class TestAIModerator(unittest.TestCase):
    def setUp(self):
        self.moderator = AIModerator("model_name", "system_instructions")

    def test_determine_next_speaker(self):
        # Test determining the next speaker by the AI moderator
        # Mock the chat.send_message() method to return a predefined response
        self.moderator.chat.send_message = lambda prompt: Mock(text="Alex")

        chat_history = [
            {"role": "user", "name": "John", "text": "Hello"},
            {"role": "model", "name": "AI", "text": "Hi there!"}
        ]
        next_speaker = self.moderator.determine_next_speaker(chat_history)
        self.assertEqual(next_speaker, "Alex")

if __name__ == '__main__':
    unittest.main()
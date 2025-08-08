"""
Tests for LlamaLot data models.
"""

import sys
import os
import unittest
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llamalot.models import (
    OllamaModel, ModelDetails, ModelInfo,
    ChatMessage, ChatConversation, MessageRole,
    ApplicationConfig, OllamaServerConfig
)


class TestOllamaModel(unittest.TestCase):
    """Test OllamaModel data class."""
    
    def test_model_creation(self):
        """Test creating a model from scratch."""
        details = ModelDetails(
            format="gguf",
            family="llama",
            parameter_size="7B",
            quantization_level="Q4_0"
        )
        
        model = OllamaModel(
            name="llama3:latest",
            modified_at=datetime.now(),
            size=3825819519,
            digest="fe938a131f40e6f6d40083c9f0f430a515233eb2edaa6d72eb85c50d64f2300e",
            details=details
        )
        
        self.assertEqual(model.name, "llama3:latest")
        self.assertEqual(model.short_name, "llama3")
        self.assertEqual(model.tag, "latest")
        self.assertIn("GB", model.size_human_readable)
    
    def test_model_from_api_response(self):
        """Test creating model from API response format."""
        api_response = {
            "name": "codellama:13b",
            "modified_at": "2023-11-04T14:56:49.277302595-07:00",
            "size": 7365960935,
            "digest": "9f438cb9cd581fc025612d27f7c1a6669ff83a8bb0ed86c94fcf4c5440555697",
            "details": {
                "format": "gguf",
                "family": "llama",
                "parameter_size": "13B",
                "quantization_level": "Q4_0"
            }
        }
        
        model = OllamaModel.from_list_response(api_response)
        
        self.assertEqual(model.name, "codellama:13b")
        self.assertEqual(model.details.family, "llama")
        self.assertEqual(model.details.parameter_size, "13B")
        self.assertFalse(model.is_cached)
    
    def test_model_serialization(self):
        """Test converting model to/from dictionary."""
        model = OllamaModel(
            name="test:latest",
            modified_at=datetime.now(),
            size=1000000,
            digest="abc123",
            details=ModelDetails(family="test")
        )
        
        # Convert to dict and back
        model_dict = model.to_dict()
        restored_model = OllamaModel.from_dict(model_dict)
        
        self.assertEqual(model.name, restored_model.name)
        self.assertEqual(model.size, restored_model.size)
        self.assertEqual(model.details.family, restored_model.details.family)


class TestChatMessage(unittest.TestCase):
    """Test ChatMessage data class."""
    
    def test_user_message_creation(self):
        """Test creating user messages."""
        message = ChatMessage.create_user_message("Hello, how are you?")
        
        self.assertEqual(message.role, MessageRole.USER)
        self.assertEqual(message.content, "Hello, how are you?")
        self.assertIsInstance(message.timestamp, datetime)
    
    def test_assistant_message_creation(self):
        """Test creating assistant messages."""
        message = ChatMessage.create_assistant_message(
            "I'm doing well, thank you!",
            model_name="llama3",
            tokens_used=25,
            generation_time=1.5
        )
        
        self.assertEqual(message.role, MessageRole.ASSISTANT)
        self.assertEqual(message.model_name, "llama3")
        self.assertEqual(message.tokens_used, 25)
        self.assertEqual(message.generation_time, 1.5)
    
    def test_message_serialization(self):
        """Test converting message to/from dictionary."""
        message = ChatMessage.create_user_message("Test message")
        
        # Convert to dict and back
        message_dict = message.to_dict()
        restored_message = ChatMessage.from_dict(message_dict)
        
        self.assertEqual(message.content, restored_message.content)
        self.assertEqual(message.role, restored_message.role)
    
    def test_ollama_format(self):
        """Test converting to Ollama API format."""
        message = ChatMessage.create_user_message("Test message")
        ollama_format = message.to_ollama_format()
        
        self.assertEqual(ollama_format['role'], 'user')
        self.assertEqual(ollama_format['content'], 'Test message')
        self.assertIsInstance(ollama_format, dict)


class TestChatConversation(unittest.TestCase):
    """Test ChatConversation data class."""
    
    def test_conversation_creation(self):
        """Test creating a conversation."""
        conv = ChatConversation(
            conversation_id="test-123",
            title="Test Conversation",
            model_name="llama3"
        )
        
        self.assertEqual(conv.conversation_id, "test-123")
        self.assertEqual(conv.title, "Test Conversation")
        self.assertEqual(conv.message_count, 0)
    
    def test_adding_messages(self):
        """Test adding messages to conversation."""
        conv = ChatConversation("test-123", "Test")
        
        user_msg = ChatMessage.create_user_message("Hello")
        assistant_msg = ChatMessage.create_assistant_message("Hi there!")
        
        conv.add_message(user_msg)
        conv.add_message(assistant_msg)
        
        self.assertEqual(conv.message_count, 2)
        self.assertEqual(conv.user_message_count, 1)
        self.assertEqual(conv.assistant_message_count, 1)
    
    def test_api_format(self):
        """Test getting messages in API format."""
        conv = ChatConversation("test-123", "Test", system_prompt="You are helpful")
        
        user_msg = ChatMessage.create_user_message("Hello")
        conv.add_message(user_msg)
        
        api_messages = conv.get_messages_for_api()
        
        # Should have system message + user message
        self.assertEqual(len(api_messages), 2)
        self.assertEqual(api_messages[0]['role'], 'system')
        self.assertEqual(api_messages[1]['role'], 'user')


class TestApplicationConfig(unittest.TestCase):
    """Test ApplicationConfig data class."""
    
    def test_default_config(self):
        """Test creating default configuration."""
        config = ApplicationConfig()
        
        self.assertEqual(config.ollama_server.host, "localhost")
        self.assertEqual(config.ollama_server.port, 11434)
        self.assertIsNotNone(config.data_directory)
        self.assertTrue(config.first_run)
    
    def test_config_serialization(self):
        """Test configuration serialization."""
        config = ApplicationConfig()
        config.ollama_server.host = "example.com"
        config.ui_preferences.window_width = 1000
        
        # Convert to dict and back
        config_dict = config.to_dict()
        restored_config = ApplicationConfig.from_dict(config_dict)
        
        self.assertEqual(config.ollama_server.host, restored_config.ollama_server.host)
        self.assertEqual(config.ui_preferences.window_width, restored_config.ui_preferences.window_width)
    
    def test_server_urls(self):
        """Test server URL generation."""
        config = OllamaServerConfig(host="example.com", port=8080, use_https=True)
        
        self.assertEqual(config.base_url, "https://example.com:8080")
        self.assertEqual(config.api_url, "https://example.com:8080/api")


if __name__ == "__main__":
    unittest.main()

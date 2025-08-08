#!/usr/bin/env python3
"""
Demo script to show the data models in action.
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from llamalot.models import (
    OllamaModel, ModelDetails,
    ChatMessage, ChatConversation, MessageRole,
    ApplicationConfig
)


def demo_ollama_model():
    """Demonstrate OllamaModel functionality."""
    print("=== Ollama Model Demo ===")
    
    # Simulate API response data
    api_data = {
        "name": "llama3:8b",
        "modified_at": "2024-08-07T21:30:00.000Z",
        "size": 4661224676,
        "digest": "365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1",
        "details": {
            "format": "gguf",
            "family": "llama",
            "parameter_size": "8.0B",
            "quantization_level": "Q4_0"
        }
    }
    
    # Create model from API response
    model = OllamaModel.from_list_response(api_data)
    
    print(f"Model: {model}")
    print(f"Short name: {model.short_name}")
    print(f"Tag: {model.tag}")
    print(f"Size: {model.size_human_readable}")
    print(f"Family: {model.details.family}")
    print(f"Parameters: {model.details.parameter_size}")
    print(f"Cached: {model.is_cached}")
    print()


def demo_chat_conversation():
    """Demonstrate chat conversation functionality."""
    print("=== Chat Conversation Demo ===")
    
    # Create a conversation
    conv = ChatConversation(
        conversation_id="demo-chat-001",
        title="Demo Chat",
        model_name="llama3:8b",
        system_prompt="You are a helpful assistant."
    )
    
    # Add some messages
    user_msg1 = ChatMessage.create_user_message("Hello! What's the weather like?")
    conv.add_message(user_msg1)
    
    assistant_msg1 = ChatMessage.create_assistant_message(
        "I don't have access to real-time weather data, but I'd be happy to help you find that information!",
        model_name="llama3:8b",
        tokens_used=28,
        generation_time=1.2
    )
    conv.add_message(assistant_msg1)
    
    user_msg2 = ChatMessage.create_user_message("Thanks! Can you help me with Python programming instead?")
    conv.add_message(user_msg2)
    
    assistant_msg2 = ChatMessage.create_assistant_message(
        "Absolutely! I'd be happy to help you with Python programming. What specific topic or problem would you like to work on?",
        model_name="llama3:8b",
        tokens_used=32,
        generation_time=1.4
    )
    conv.add_message(assistant_msg2)
    
    print(f"Conversation: {conv}")
    print(f"Messages: {conv.message_count}")
    print(f"User messages: {conv.user_message_count}")
    print(f"Assistant messages: {conv.assistant_message_count}")
    print(f"Total tokens: {conv.total_tokens}")
    print(f"Total time: {conv.total_time:.2f}s")
    print()
    
    # Show messages in API format
    print("Messages for API:")
    api_messages = conv.get_messages_for_api()
    for i, msg in enumerate(api_messages, 1):
        print(f"  {i}. {msg['role']}: {msg['content'][:50]}...")
    print()


def demo_configuration():
    """Demonstrate configuration functionality."""
    print("=== Configuration Demo ===")
    
    # Create default configuration
    config = ApplicationConfig()
    
    print(f"Ollama server: {config.ollama_server.base_url}")
    print(f"Data directory: {config.data_directory}")
    print(f"Window size: {config.ui_preferences.window_width}x{config.ui_preferences.window_height}")
    print(f"Chat temperature: {config.chat_defaults.temperature}")
    print(f"Stream responses: {config.chat_defaults.stream_responses}")
    print()
    
    # Demonstrate serialization
    print("Config as dictionary (first few keys):")
    config_dict = config.to_dict()
    for key in list(config_dict.keys())[:5]:
        print(f"  {key}: {config_dict[key]}")
    print("  ...")
    print()


def main():
    """Run all demonstrations."""
    print("LlamaLot Data Models Demonstration")
    print("=" * 40)
    print()
    
    demo_ollama_model()
    demo_chat_conversation()
    demo_configuration()
    
    print("Demo completed successfully!")


if __name__ == "__main__":
    main()

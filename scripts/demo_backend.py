#!/usr/bin/env python3
"""
Demo script for testing LlamaLot backend components.

This script demonstrates the configuration management and basic functionality
without requiring external dependencies like the ollama library.
"""

import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from llamalot.backend.config import ConfigurationManager, get_config_manager, get_config
from llamalot.models import ApplicationConfig, OllamaModel, ChatMessage, ChatConversation


def test_configuration_management():
    """Test configuration management functionality."""
    print("=" * 60)
    print("Testing Configuration Management")
    print("=" * 60)
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_config_path = Path(f.name)
    
    try:
        # Test configuration manager
        manager = ConfigurationManager(temp_config_path)
        
        print("1. Testing configuration loading...")
        config = manager.config
        print(f"   ✓ Default host: {config.ollama_server.host}")
        print(f"   ✓ Default port: {config.ollama_server.port}")
        print(f"   ✓ Window size: {config.ui_preferences.window_width}x{config.ui_preferences.window_height}")
        
        print("\n2. Testing configuration updates...")
        manager.update_ollama_server("demo.example.com", 8080, True)
        print(f"   ✓ Updated server: {config.ollama_server.base_url}")
        
        manager.update_ui_preferences(theme="dark", window_width=1400)
        print(f"   ✓ Updated theme: {config.ui_preferences.theme}")
        print(f"   ✓ Updated width: {config.ui_preferences.window_width}")
        
        manager.update_chat_defaults(temperature=0.9, top_p=0.8)
        print(f"   ✓ Updated temperature: {config.chat_defaults.temperature}")
        print(f"   ✓ Updated top_p: {config.chat_defaults.top_p}")
        
        print("\n3. Testing configuration save/load...")
        saved = manager.save()
        print(f"   ✓ Configuration saved: {saved}")
        
        # Load in new manager to verify persistence
        new_manager = ConfigurationManager(temp_config_path)
        loaded_config = new_manager.load()
        print(f"   ✓ Loaded server: {loaded_config.ollama_server.base_url}")
        print(f"   ✓ Loaded theme: {loaded_config.ui_preferences.theme}")
        
        print("\n4. Testing configuration validation...")
        validation = manager.validate_config()
        print(f"   ✓ Config valid: {validation['valid']}")
        print(f"   ✓ Errors: {len(validation['errors'])}")
        print(f"   ✓ Warnings: {len(validation['warnings'])}")
        
        print("\n5. Testing directory management...")
        try:
            data_dir = manager.get_data_directory()
            print(f"   ✓ Data directory: {data_dir}")
        except ValueError as e:
            print(f"   ! Data directory not configured: {e}")
        
        # Test global configuration manager
        print("\n6. Testing global configuration manager...")
        global_manager = get_config_manager()
        global_config = get_config()
        print(f"   ✓ Global manager type: {type(global_manager).__name__}")
        print(f"   ✓ Global config type: {type(global_config).__name__}")
        
    finally:
        # Clean up
        if temp_config_path.exists():
            temp_config_path.unlink()


def test_data_models():
    """Test data model functionality."""
    print("\n" + "=" * 60)
    print("Testing Data Models")
    print("=" * 60)
    
    print("1. Testing OllamaModel...")
    from datetime import datetime
    model = OllamaModel(
        name="llama3.2:3b",
        size=2000000000,
        digest="abc123def456",
        modified_at=datetime.now()
    )
    print(f"   ✓ Model name: {model.name}")
    print(f"   ✓ Model size: {model.size_human_readable}")
    print(f"   ✓ Model short name: {model.short_name}")
    print(f"   ✓ Model tag: {model.tag}")
    print(f"   ✓ Model details family: {model.details.family}")
    
    print(f"\n   Testing with details...")
    model.details.family = "llama"
    model.details.parameter_size = "3B"
    model.details.quantization_level = "Q4_0"
    print(f"   ✓ Model family: {model.details.family}")
    print(f"   ✓ Parameter size: {model.details.parameter_size}")
    print(f"   ✓ Quantization: {model.details.quantization_level}")
    
    print("\n2. Testing ChatMessage...")
    message = ChatMessage(
        role="user",
        content="Hello, how are you?",
        model_name="llama3.2:3b"
    )
    print(f"   ✓ Message role: {message.role}")
    print(f"   ✓ Message content: {message.content}")
    print(f"   ✓ Message model: {message.model_name}")
    
    api_dict = message.to_ollama_format()
    print(f"   ✓ API format keys: {list(api_dict.keys())}")
    
    print("\n3. Testing ChatConversation...")
    conversation = ChatConversation(
        conversation_id="demo-conv-1",
        title="Demo Conversation",
        model_name="llama3.2:3b"
    )
    conversation.add_message(message)
    
    response = ChatMessage(
        role="assistant", 
        content="Hello! I'm doing well, thank you for asking.",
        model_name="llama3.2:3b"
    )
    conversation.add_message(response)
    
    print(f"   ✓ Conversation length: {len(conversation.messages)}")
    if conversation.messages:
        last_msg = conversation.messages[-1]
        print(f"   ✓ Last message: {last_msg.content[:50]}...")
    
    api_messages = conversation.get_messages_for_api()
    print(f"   ✓ API messages count: {len(api_messages)}")
    
    print("\n4. Testing serialization...")
    model_dict = model.to_dict()
    restored_model = OllamaModel.from_dict(model_dict)
    print(f"   ✓ Model serialization: {model.name == restored_model.name}")
    
    conv_dict = conversation.to_dict()
    restored_conv = ChatConversation.from_dict(conv_dict)
    print(f"   ✓ Conversation serialization: {len(conversation.messages) == len(restored_conv.messages)}")


def test_ollama_client_structure():
    """Test Ollama client structure (without actual Ollama connection)."""
    print("\n" + "=" * 60)
    print("Testing Ollama Client Structure")
    print("=" * 60)
    
    try:
        from llamalot.backend.ollama_client import OllamaConnectionError, OllamaModelNotFoundError
        print("1. Testing exception classes...")
        print(f"   ✓ OllamaConnectionError imported")
        print(f"   ✓ OllamaModelNotFoundError imported")
        
        # Test exception creation
        conn_error = OllamaConnectionError("Test connection error")
        model_error = OllamaModelNotFoundError("Test model not found")
        print(f"   ✓ Connection error: {conn_error}")
        print(f"   ✓ Model error: {model_error}")
        
    except ImportError as e:
        print(f"! Could not import Ollama client (expected - ollama library not installed): {e}")
        print("  This is normal in a development environment without ollama-python installed.")


def main():
    """Run all tests."""
    print("LlamaLot Backend Demo")
    print("Testing core functionality without external dependencies")
    
    test_configuration_management()
    test_data_models()
    test_ollama_client_structure()
    
    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Install ollama-python: pip install ollama")
    print("2. Install wxPython: pip install wxpython")
    print("3. Run the full application: python main.py")


if __name__ == "__main__":
    main()

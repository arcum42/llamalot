"""
Data models package for LlamaLot application.

Contains data classes and models representing:
- Ollama model information (OllamaModel, ModelDetails, ModelInfo)
- Chat messages and conversations (ChatMessage, ChatConversation, ChatImage)
- Configuration settings (ApplicationConfig, OllamaServerConfig, UIPreferences)
- Database schemas
"""

from .ollama_model import OllamaModel, ModelDetails, ModelInfo
from .chat import (
    ChatMessage, 
    ChatConversation, 
    ChatImage, 
    MessageRole, 
    ToolCall
)
from .config import (
    ApplicationConfig, 
    OllamaServerConfig, 
    UIPreferences, 
    ChatDefaults
)

__all__ = [
    # Ollama model classes
    'OllamaModel',
    'ModelDetails', 
    'ModelInfo',
    
    # Chat classes
    'ChatMessage',
    'ChatConversation',
    'ChatImage',
    'MessageRole',
    'ToolCall',
    
    # Configuration classes
    'ApplicationConfig',
    'OllamaServerConfig',
    'UIPreferences',
    'ChatDefaults',
]

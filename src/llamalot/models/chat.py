"""
Chat-related data models for LlamaLot application.

Represents chat messages, conversations, and related metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum
import base64


class MessageRole(Enum):
    """Enumeration of possible message roles in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ToolCall:
    """Represents a tool call made by the assistant."""
    function_name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None


@dataclass
class ChatImage:
    """Represents an image attached to a chat message."""
    
    # Image data (base64 encoded)
    data: str
    
    # Metadata
    filename: Optional[str] = None
    mime_type: Optional[str] = None
    size: Optional[int] = None
    source_path: Optional[str] = None  # Original file path for batch processing
    
    @classmethod
    def from_file_path(cls, file_path: str) -> 'ChatImage':
        """
        Create a ChatImage from a file path.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            ChatImage instance with base64-encoded data
        """
        import mimetypes
        import os
        
        try:
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            # Encode to base64
            encoded_data = base64.b64encode(image_data).decode('utf-8')
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            
            return cls(
                data=encoded_data,
                filename=os.path.basename(file_path),
                mime_type=mime_type,
                size=len(image_data),
                source_path=file_path
            )
        except Exception as e:
            raise ValueError(f"Could not load image from {file_path}: {e}")
    
    @property
    def size_human_readable(self) -> str:
        """Return human-readable size string."""
        if not self.size:
            return "Unknown"
        
        size = float(self.size)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


@dataclass
class ChatMessage:
    """Represents a single message in a chat conversation."""
    
    # Core message data
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Optional attachments and metadata
    images: List[ChatImage] = field(default_factory=list)
    tool_calls: List[ToolCall] = field(default_factory=list)
    
    # Message metadata
    message_id: Optional[str] = None
    model_name: Optional[str] = None  # Which model generated this (for assistant messages)
    tokens_used: Optional[int] = None
    generation_time: Optional[float] = None  # Time in seconds
    
    # Error information
    error: Optional[str] = None
    is_error: bool = False
    
    def __post_init__(self):
        """Post-initialization processing."""
        if isinstance(self.role, str):
            self.role = MessageRole(self.role)
    
    @classmethod
    def create_user_message(cls, content: str, images: Optional[List[ChatImage]] = None) -> 'ChatMessage':
        """Create a user message."""
        return cls(
            role=MessageRole.USER,
            content=content,
            images=images or []
        )
    
    @classmethod
    def create_assistant_message(
        cls, 
        content: str, 
        model_name: Optional[str] = None,
        tokens_used: Optional[int] = None,
        generation_time: Optional[float] = None
    ) -> 'ChatMessage':
        """Create an assistant message."""
        return cls(
            role=MessageRole.ASSISTANT,
            content=content,
            model_name=model_name,
            tokens_used=tokens_used,
            generation_time=generation_time
        )
    
    @classmethod
    def create_system_message(cls, content: str) -> 'ChatMessage':
        """Create a system message."""
        return cls(
            role=MessageRole.SYSTEM,
            content=content
        )
    
    @classmethod
    def create_error_message(cls, error_text: str) -> 'ChatMessage':
        """Create an error message."""
        return cls(
            role=MessageRole.ASSISTANT,
            content=f"Error: {error_text}",
            error=error_text,
            is_error=True
        )
    
    def to_ollama_format(self) -> Dict[str, Any]:
        """
        Convert to the format expected by Ollama chat API.
        
        Returns:
            Dictionary in Ollama chat message format
        """
        message: Dict[str, Any] = {
            'role': self.role.value,
            'content': self.content
        }
        
        # Add images if present (for multimodal models)
        if self.images:
            message['images'] = [img.data for img in self.images]
        
        # Add tool calls if present
        if self.tool_calls:
            message['tool_calls'] = [
                {
                    'function': {
                        'name': call.function_name,
                        'arguments': call.arguments
                    }
                }
                for call in self.tool_calls
            ]
        
        return message
    
    @classmethod
    def from_ollama_response(cls, response_data: Dict[str, Any], model_name: Optional[str] = None) -> 'ChatMessage':
        """
        Create a ChatMessage from an Ollama chat response.
        
        Args:
            response_data: Response dictionary from Ollama chat API
            model_name: Name of the model that generated the response
            
        Returns:
            ChatMessage instance
        """
        message_data = response_data.get('message', {})
        
        # Extract token and timing information
        tokens_used = None
        generation_time = None
        
        if 'eval_count' in response_data and 'eval_duration' in response_data:
            tokens_used = response_data['eval_count']
            # Convert nanoseconds to seconds
            generation_time = response_data['eval_duration'] / 1_000_000_000
        
        return cls(
            role=MessageRole(message_data.get('role', 'assistant')),
            content=message_data.get('content', ''),
            model_name=model_name,
            tokens_used=tokens_used,
            generation_time=generation_time
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'role': self.role.value,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'images': [
                {
                    'data': img.data,
                    'filename': img.filename,
                    'mime_type': img.mime_type,
                    'size': img.size
                }
                for img in self.images
            ],
            'tool_calls': [
                {
                    'function_name': call.function_name,
                    'arguments': call.arguments,
                    'call_id': call.call_id
                }
                for call in self.tool_calls
            ],
            'message_id': self.message_id,
            'model_name': self.model_name,
            'tokens_used': self.tokens_used,
            'generation_time': self.generation_time,
            'error': self.error,
            'is_error': self.is_error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create from dictionary."""
        # Parse timestamp
        timestamp = datetime.fromisoformat(data['timestamp'])
        
        # Parse images
        images = []
        for img_data in data.get('images', []):
            images.append(ChatImage(
                data=img_data['data'],
                filename=img_data.get('filename'),
                mime_type=img_data.get('mime_type'),
                size=img_data.get('size')
            ))
        
        # Parse tool calls
        tool_calls = []
        for call_data in data.get('tool_calls', []):
            tool_calls.append(ToolCall(
                function_name=call_data['function_name'],
                arguments=call_data['arguments'],
                call_id=call_data.get('call_id')
            ))
        
        return cls(
            role=MessageRole(data['role']),
            content=data['content'],
            timestamp=timestamp,
            images=images,
            tool_calls=tool_calls,
            message_id=data.get('message_id'),
            model_name=data.get('model_name'),
            tokens_used=data.get('tokens_used'),
            generation_time=data.get('generation_time'),
            error=data.get('error'),
            is_error=data.get('is_error', False)
        )
    
    @property
    def display_timestamp(self) -> str:
        """Return a formatted timestamp for display."""
        return self.timestamp.strftime("%H:%M:%S")
    
    def __str__(self) -> str:
        """String representation."""
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"ChatMessage({self.role.value}: '{preview}')"


@dataclass
class ChatConversation:
    """Represents a complete chat conversation."""
    
    # Conversation metadata
    conversation_id: str
    title: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Messages in the conversation
    messages: List[ChatMessage] = field(default_factory=list)
    
    # Model information
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None
    
    # Conversation statistics
    total_tokens: int = 0
    total_time: float = 0.0
    
    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        self.updated_at = datetime.now()
        
        # Update statistics
        if message.tokens_used:
            self.total_tokens += message.tokens_used
        if message.generation_time:
            self.total_time += message.generation_time
    
    def get_messages_for_api(self) -> List[Dict[str, Any]]:
        """
        Get messages in the format expected by Ollama API.
        
        Returns:
            List of message dictionaries for API calls
        """
        api_messages = []
        
        # Add system message if present
        if self.system_prompt:
            api_messages.append({
                'role': 'system',
                'content': self.system_prompt
            })
        
        # Add conversation messages (excluding error messages)
        for message in self.messages:
            if not message.is_error:
                api_messages.append(message.to_ollama_format())
        
        return api_messages
    
    @property
    def message_count(self) -> int:
        """Return the number of messages in the conversation."""
        return len(self.messages)
    
    @property
    def user_message_count(self) -> int:
        """Return the number of user messages."""
        return sum(1 for msg in self.messages if msg.role == MessageRole.USER)
    
    @property
    def assistant_message_count(self) -> int:
        """Return the number of assistant messages."""
        return sum(1 for msg in self.messages if msg.role == MessageRole.ASSISTANT and not msg.is_error)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'conversation_id': self.conversation_id,
            'title': self.title,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'messages': [msg.to_dict() for msg in self.messages],
            'model_name': self.model_name,
            'system_prompt': self.system_prompt,
            'total_tokens': self.total_tokens,
            'total_time': self.total_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatConversation':
        """Create from dictionary."""
        # Parse timestamps
        created_at = datetime.fromisoformat(data['created_at'])
        updated_at = datetime.fromisoformat(data['updated_at'])
        
        # Parse messages
        messages = [ChatMessage.from_dict(msg_data) for msg_data in data.get('messages', [])]
        
        return cls(
            conversation_id=data['conversation_id'],
            title=data['title'],
            created_at=created_at,
            updated_at=updated_at,
            messages=messages,
            model_name=data.get('model_name'),
            system_prompt=data.get('system_prompt'),
            total_tokens=data.get('total_tokens', 0),
            total_time=data.get('total_time', 0.0)
        )
    
    def __str__(self) -> str:
        """String representation."""
        return f"ChatConversation('{self.title}', {self.message_count} messages, model='{self.model_name}')"

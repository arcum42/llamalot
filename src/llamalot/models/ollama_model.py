"""
Data models for representing Ollama models and their metadata.

Based on the Ollama API response formats from /api/tags and /api/show endpoints.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelDetails:
    """Detailed information about a model's format and parameters."""
    
    format: str = ""
    family: str = ""
    families: Optional[List[str]] = None
    parameter_size: str = ""
    quantization_level: str = ""
    parent_model: str = ""


@dataclass
class ModelInfo:
    """Extended model information from the /api/show endpoint."""
    
    # Architecture and technical details
    architecture: Optional[str] = None
    file_type: Optional[int] = None
    parameter_count: Optional[int] = None
    quantization_version: Optional[int] = None
    
    # Context and attention details
    attention_head_count: Optional[int] = None
    attention_head_count_kv: Optional[int] = None
    attention_layer_norm_rms_epsilon: Optional[float] = None
    block_count: Optional[int] = None
    context_length: Optional[int] = None
    embedding_length: Optional[int] = None
    feed_forward_length: Optional[int] = None
    vocab_size: Optional[int] = None
    
    # Tokenizer details
    bos_token_id: Optional[int] = None
    eos_token_id: Optional[int] = None
    tokenizer_model: Optional[str] = None
    
    # Additional metadata
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_api_response(cls, model_info_dict: Dict[str, Any]) -> 'ModelInfo':
        """Create ModelInfo from API response dictionary."""
        info = cls()
        
        # Map common fields
        general = model_info_dict.get('general', {})
        info.architecture = general.get('architecture')
        info.file_type = general.get('file_type')
        info.parameter_count = general.get('parameter_count')
        info.quantization_version = general.get('quantization_version')
        
        # Map llama-specific fields (most common)
        llama = model_info_dict.get('llama', {})
        info.attention_head_count = llama.get('attention.head_count')
        info.attention_head_count_kv = llama.get('attention.head_count_kv')
        info.attention_layer_norm_rms_epsilon = llama.get('attention.layer_norm_rms_epsilon')
        info.block_count = llama.get('block_count')
        info.context_length = llama.get('context_length')
        info.embedding_length = llama.get('embedding_length')
        info.feed_forward_length = llama.get('feed_forward_length')
        info.vocab_size = llama.get('vocab_size')
        
        # Map tokenizer fields
        tokenizer = model_info_dict.get('tokenizer', {}).get('ggml', {})
        info.bos_token_id = tokenizer.get('bos_token_id')
        info.eos_token_id = tokenizer.get('eos_token_id')
        info.tokenizer_model = tokenizer.get('model')
        
        # Store any additional data
        info.extra_data = {k: v for k, v in model_info_dict.items() 
                          if k not in ['general', 'llama', 'tokenizer']}
        
        return info


@dataclass
class OllamaModel:
    """
    Represents an Ollama model with all its metadata.
    
    This class encapsulates information from both the /api/tags list endpoint
    and the detailed /api/show endpoint.
    """
    
    # Basic model information
    name: str
    modified_at: datetime
    size: int  # Size in bytes
    digest: str
    
    # Model details
    details: ModelDetails = field(default_factory=ModelDetails)
    
    # Model capabilities (e.g., ["completion", "vision"])
    capabilities: List[str] = field(default_factory=list)
    
    # Extended model information (from /api/show)
    modelfile: Optional[str] = None
    parameters: Optional[str] = None
    template: Optional[str] = None
    system: Optional[str] = None
    model_info: Optional[ModelInfo] = None
    
    # Cache metadata
    last_updated: Optional[datetime] = None
    is_cached: bool = False
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    @classmethod
    def from_list_response(cls, model_data: Dict[str, Any]) -> 'OllamaModel':
        """
        Create an OllamaModel from the /api/tags response format.
        
        Args:
            model_data: Dictionary from the models list in /api/tags response
            
        Returns:
            OllamaModel instance with basic information populated
        """
        try:
            # Parse the modified_at timestamp
            modified_at_value = model_data.get('modified_at', '')
            if isinstance(modified_at_value, datetime):
                # Already a datetime object
                modified_at = modified_at_value
            elif isinstance(modified_at_value, str) and modified_at_value:
                try:
                    # Handle ISO format: "2023-11-04T14:56:49.277302595-07:00"
                    modified_at = datetime.fromisoformat(modified_at_value.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    modified_at = datetime.now()
            else:
                modified_at = datetime.now()
            
            # Create ModelDetails
            details_data = model_data.get('details', {})
            details = ModelDetails(
                format=details_data.get('format', ''),
                family=details_data.get('family', ''),
                families=details_data.get('families'),
                parameter_size=details_data.get('parameter_size', ''),
                quantization_level=details_data.get('quantization_level', ''),
                parent_model=details_data.get('parent_model', '')
            )
            
            # Ensure size is an integer
            size_value = model_data.get('size', 0)
            if isinstance(size_value, str):
                try:
                    size_value = int(size_value)
                except ValueError:
                    size_value = 0
            
            # Use 'model' field as the name since 'name' field is often empty
            name_value = model_data.get('model', '') or model_data.get('name', '')
            
            # Validate that we have a non-empty name
            if not name_value or not name_value.strip():
                logger.warning(f"Skipping model with empty name. Model data: {model_data}")
                raise ValueError(f"Model has empty or invalid name: {model_data}")
            
            # Detect capabilities based on model families
            capabilities = ['completion']  # All models can do text completion
            families = details_data.get('families', []) or []
            # Vision models typically have 'clip' (older models) or 'mllama' (newer models) in families
            vision_indicators = ['clip', 'mllama']
            if families and any(indicator in families for indicator in vision_indicators):
                capabilities.append('vision')
            
            return cls(
                name=name_value,
                modified_at=modified_at,
                size=size_value,
                digest=model_data.get('digest', ''),
                details=details,
                capabilities=capabilities,
                is_cached=False
            )
            
        except Exception as e:
            # Enhanced error reporting
            import traceback
            print(f"Error parsing model data: {e}")
            print(f"Model data: {model_data}")
            print(f"Traceback: {traceback.format_exc()}")
            raise
    
    def update_from_show_response(self, show_data: Dict[str, Any]) -> None:
        """
        Update the model with detailed information from /api/show response.
        
        Args:
            show_data: Dictionary from /api/show response
        """
        self.modelfile = show_data.get('modelfile')
        self.parameters = show_data.get('parameters')
        self.template = show_data.get('template')
        self.system = show_data.get('system')
        
        # Update model info if available
        model_info_data = show_data.get('model_info')
        if model_info_data:
            self.model_info = ModelInfo.from_api_response(model_info_data)
        
        self.last_updated = datetime.now()
        self.is_cached = True
    
    @property
    def size_human_readable(self) -> str:
        """Return human-readable size string."""
        if self.size == 0:
            return "Unknown"
        
        # Convert bytes to human readable format
        size_bytes = float(self.size)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    @property
    def short_name(self) -> str:
        """Return the model name without the tag if present."""
        return self.name.split(':')[0]
    
    @property
    def tag(self) -> str:
        """Return the tag part of the model name, or 'latest' if none."""
        parts = self.name.split(':')
        return parts[1] if len(parts) > 1 else 'latest'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary for serialization."""
        return {
            'name': self.name,
            'modified_at': self.modified_at.isoformat(),
            'size': self.size,
            'digest': self.digest,
            'details': {
                'format': self.details.format,
                'family': self.details.family,
                'families': self.details.families,
                'parameter_size': self.details.parameter_size,
                'quantization_level': self.details.quantization_level,
                'parent_model': self.details.parent_model,
            },
            'modelfile': self.modelfile,
            'parameters': self.parameters,
            'template': self.template,
            'system': self.system,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'is_cached': self.is_cached,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OllamaModel':
        """Create an OllamaModel from a dictionary."""
        # Parse timestamps
        modified_at = datetime.fromisoformat(data['modified_at'])
        last_updated = None
        if data.get('last_updated'):
            last_updated = datetime.fromisoformat(data['last_updated'])
        
        # Create details
        details_data = data.get('details', {})
        details = ModelDetails(
            format=details_data.get('format', ''),
            family=details_data.get('family', ''),
            families=details_data.get('families'),
            parameter_size=details_data.get('parameter_size', ''),
            quantization_level=details_data.get('quantization_level', ''),
            parent_model=details_data.get('parent_model', '')
        )
        
        return cls(
            name=data['name'],
            modified_at=modified_at,
            size=data['size'],
            digest=data['digest'],
            details=details,
            modelfile=data.get('modelfile'),
            parameters=data.get('parameters'),
            template=data.get('template'),
            system=data.get('system'),
            last_updated=last_updated,
            is_cached=data.get('is_cached', False)
        )
    
    def __str__(self) -> str:
        """String representation of the model."""
        return f"OllamaModel(name='{self.name}', size='{self.size_human_readable}', family='{self.details.family}')"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"OllamaModel(name='{self.name}', modified_at='{self.modified_at}', "
                f"size={self.size}, digest='{self.digest[:16]}...', "
                f"family='{self.details.family}', cached={self.is_cached})")

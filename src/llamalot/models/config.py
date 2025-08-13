"""
Configuration data models for LlamaLot application.

Handles application settings, preferences, and configuration management.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
import os


@dataclass
class OllamaServerConfig:
    """Configuration for Ollama server connection."""
    
    host: str = "localhost"
    port: int = 11434
    use_https: bool = False
    timeout: int = 30
    
    @property
    def base_url(self) -> str:
        """Get the full base URL for the Ollama server."""
        protocol = "https" if self.use_https else "http"
        return f"{protocol}://{self.host}:{self.port}"
    
    @property
    def api_url(self) -> str:
        """Get the API base URL."""
        return f"{self.base_url}/api"


@dataclass
class UIPreferences:
    """User interface preferences and settings."""
    
    # Window settings
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    
    # Model list settings
    model_list_sort_column: str = "name"
    model_list_sort_ascending: bool = True
    show_model_details: bool = True
    
    # Model selection
    default_model: Optional[str] = None  # Name of model to auto-select on startup
    auto_select_default_model: bool = True
    
    # Chat settings
    chat_font_size: int = 12
    chat_font_family: str = "Default"
    show_timestamps: bool = True
    use_ai_generated_titles: bool = True  # Generate smart titles using AI for longer conversations
    auto_scroll_chat: bool = True
    
    # Theme and appearance
    theme: str = "default"  # "default", "dark", "light"
    
    # Model management
    confirm_model_deletion: bool = True
    auto_refresh_models: bool = True
    refresh_interval_minutes: int = 5


@dataclass
class ChatDefaults:
    """Default settings for chat conversations."""
    
    # Default model parameters
    temperature: float = 0.8
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    
    # Context settings
    context_length: int = 2048
    keep_alive: str = "5m"
    
    # System prompt
    default_system_prompt: Optional[str] = None
    
    # Streaming
    stream_responses: bool = True


@dataclass
class EmbeddingsConfig:
    """Configuration for embeddings and RAG functionality."""
    
    # Default embedding model
    default_model: str = "nomic-embed-text"
    
    # RAG settings
    rag_enabled: bool = False
    active_collections: List[str] = field(default_factory=list)
    
    # Document processing
    chunk_size: int = 2000
    chunk_overlap: int = 200
    
    # Search settings
    search_results_limit: int = 5
    similarity_threshold: float = 0.7
    
    # Collection management
    auto_create_collections: bool = True
    default_collection_name: str = "documents"
    
    # ChromaDB settings
    persist_directory: Optional[str] = None  # Will be set to data_directory/embeddings by default


@dataclass
class ApplicationConfig:
    """Main application configuration."""
    
    # Server configuration
    ollama_server: OllamaServerConfig = field(default_factory=OllamaServerConfig)
    
    # UI preferences
    ui_preferences: UIPreferences = field(default_factory=UIPreferences)
    
    # Chat defaults
    chat_defaults: ChatDefaults = field(default_factory=ChatDefaults)
    
    # Embeddings configuration
    embeddings: EmbeddingsConfig = field(default_factory=EmbeddingsConfig)
    
    # Data directories
    data_directory: Optional[str] = None
    cache_directory: Optional[str] = None
    logs_directory: Optional[str] = None
    
    # Database settings
    database_file: Optional[str] = None
    cache_expiry_hours: int = 24
    
    # Logging settings
    log_level: str = "INFO"
    log_to_file: bool = True
    max_log_size_mb: int = 10
    log_backup_count: int = 5
    
    # Application metadata
    first_run: bool = True
    last_model_refresh: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization setup."""
        if self.data_directory is None:
            self.data_directory = str(self.get_default_data_directory())
        
        if self.cache_directory is None:
            self.cache_directory = str(Path(self.data_directory) / "cache")
        
        if self.logs_directory is None:
            self.logs_directory = str(Path(self.data_directory) / "logs")
        
        if self.database_file is None:
            self.database_file = str(Path(self.data_directory) / "llamalot.db")
        
        # Set embeddings persist directory if not specified
        if self.embeddings.persist_directory is None:
            self.embeddings.persist_directory = str(Path(self.data_directory) / "embeddings")
    
    @staticmethod
    def get_default_data_directory() -> Path:
        """Get the default data directory for the application."""
        home = Path.home()
        
        # Platform-specific data directories
        if os.name == 'nt':  # Windows
            data_dir = home / "AppData" / "Local" / "LlamaLot"
        elif os.name == 'posix':
            if 'darwin' in os.uname().sysname.lower():  # macOS
                data_dir = home / "Library" / "Application Support" / "LlamaLot"
            else:  # Linux and other Unix-like
                data_dir = home / ".llamalot"
        else:
            # Fallback
            data_dir = home / ".llamalot"
        
        return data_dir
    
    @staticmethod
    def get_config_file_path() -> Path:
        """Get the path to the configuration file."""
        return ApplicationConfig.get_default_data_directory() / "config.json"
    
    def ensure_directories(self) -> None:
        """Ensure all necessary directories exist."""
        directories = [
            self.data_directory,
            self.cache_directory,
            self.logs_directory,
            self.embeddings.persist_directory
        ]
        
        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
    
    def save_to_file(self, config_path: Optional[Path] = None) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            config_path: Path to save config file (default: standard location)
        """
        if config_path is None:
            config_path = self.get_config_file_path()
        
        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dictionary
        config_dict = self.to_dict()
        
        # Write to file
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, config_path: Optional[Path] = None) -> 'ApplicationConfig':
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to config file (default: standard location)
            
        Returns:
            ApplicationConfig instance
        """
        if config_path is None:
            config_path = cls.get_config_file_path()
        
        if not config_path.exists():
            # Return default configuration
            config = cls()
            config.ensure_directories()
            return config
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            return cls.from_dict(config_dict)
        
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # Return default configuration if file is corrupted
            print(f"Warning: Could not load config file {config_path}: {e}")
            config = cls()
            config.ensure_directories()
            return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'ollama_server': {
                'host': self.ollama_server.host,
                'port': self.ollama_server.port,
                'use_https': self.ollama_server.use_https,
                'timeout': self.ollama_server.timeout,
            },
            'ui_preferences': {
                'window_width': self.ui_preferences.window_width,
                'window_height': self.ui_preferences.window_height,
                'window_maximized': self.ui_preferences.window_maximized,
                'model_list_sort_column': self.ui_preferences.model_list_sort_column,
                'model_list_sort_ascending': self.ui_preferences.model_list_sort_ascending,
                'show_model_details': self.ui_preferences.show_model_details,
                'default_model': self.ui_preferences.default_model,
                'auto_select_default_model': self.ui_preferences.auto_select_default_model,
                'chat_font_size': self.ui_preferences.chat_font_size,
                'chat_font_family': self.ui_preferences.chat_font_family,
                'show_timestamps': self.ui_preferences.show_timestamps,
                'auto_scroll_chat': self.ui_preferences.auto_scroll_chat,
                'theme': self.ui_preferences.theme,
                'confirm_model_deletion': self.ui_preferences.confirm_model_deletion,
                'auto_refresh_models': self.ui_preferences.auto_refresh_models,
                'refresh_interval_minutes': self.ui_preferences.refresh_interval_minutes,
            },
            'chat_defaults': {
                'temperature': self.chat_defaults.temperature,
                'top_p': self.chat_defaults.top_p,
                'top_k': self.chat_defaults.top_k,
                'repeat_penalty': self.chat_defaults.repeat_penalty,
                'context_length': self.chat_defaults.context_length,
                'keep_alive': self.chat_defaults.keep_alive,
                'default_system_prompt': self.chat_defaults.default_system_prompt,
                'stream_responses': self.chat_defaults.stream_responses,
            },
            'embeddings': {
                'default_model': self.embeddings.default_model,
                'rag_enabled': self.embeddings.rag_enabled,
                'active_collections': self.embeddings.active_collections,
                'chunk_size': self.embeddings.chunk_size,
                'chunk_overlap': self.embeddings.chunk_overlap,
                'search_results_limit': self.embeddings.search_results_limit,
                'similarity_threshold': self.embeddings.similarity_threshold,
                'auto_create_collections': self.embeddings.auto_create_collections,
                'default_collection_name': self.embeddings.default_collection_name,
                'persist_directory': self.embeddings.persist_directory,
            },
            'data_directory': self.data_directory,
            'cache_directory': self.cache_directory,
            'logs_directory': self.logs_directory,
            'database_file': self.database_file,
            'cache_expiry_hours': self.cache_expiry_hours,
            'log_level': self.log_level,
            'log_to_file': self.log_to_file,
            'max_log_size_mb': self.max_log_size_mb,
            'log_backup_count': self.log_backup_count,
            'first_run': self.first_run,
            'last_model_refresh': self.last_model_refresh,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationConfig':
        """Create configuration from dictionary."""
        # Create server config
        server_data = data.get('ollama_server', {})
        ollama_server = OllamaServerConfig(
            host=server_data.get('host', 'localhost'),
            port=server_data.get('port', 11434),
            use_https=server_data.get('use_https', False),
            timeout=server_data.get('timeout', 30)
        )
        
        # Create UI preferences
        ui_data = data.get('ui_preferences', {})
        ui_preferences = UIPreferences(
            window_width=ui_data.get('window_width', 1200),
            window_height=ui_data.get('window_height', 800),
            window_maximized=ui_data.get('window_maximized', False),
            model_list_sort_column=ui_data.get('model_list_sort_column', 'name'),
            model_list_sort_ascending=ui_data.get('model_list_sort_ascending', True),
            show_model_details=ui_data.get('show_model_details', True),
            default_model=ui_data.get('default_model'),
            auto_select_default_model=ui_data.get('auto_select_default_model', True),
            chat_font_size=ui_data.get('chat_font_size', 12),
            chat_font_family=ui_data.get('chat_font_family', 'Default'),
            show_timestamps=ui_data.get('show_timestamps', True),
            auto_scroll_chat=ui_data.get('auto_scroll_chat', True),
            theme=ui_data.get('theme', 'default'),
            confirm_model_deletion=ui_data.get('confirm_model_deletion', True),
            auto_refresh_models=ui_data.get('auto_refresh_models', True),
            refresh_interval_minutes=ui_data.get('refresh_interval_minutes', 5)
        )
        
        # Create chat defaults
        chat_data = data.get('chat_defaults', {})
        chat_defaults = ChatDefaults(
            temperature=chat_data.get('temperature', 0.8),
            top_p=chat_data.get('top_p', 0.9),
            top_k=chat_data.get('top_k', 40),
            repeat_penalty=chat_data.get('repeat_penalty', 1.1),
            context_length=chat_data.get('context_length', 2048),
            keep_alive=chat_data.get('keep_alive', '5m'),
            default_system_prompt=chat_data.get('default_system_prompt'),
            stream_responses=chat_data.get('stream_responses', True)
        )
        
        # Create embeddings config
        embeddings_data = data.get('embeddings', {})
        embeddings = EmbeddingsConfig(
            default_model=embeddings_data.get('default_model', 'nomic-embed-text'),
            rag_enabled=embeddings_data.get('rag_enabled', False),
            active_collections=embeddings_data.get('active_collections', []),
            chunk_size=embeddings_data.get('chunk_size', 2000),
            chunk_overlap=embeddings_data.get('chunk_overlap', 200),
            search_results_limit=embeddings_data.get('search_results_limit', 5),
            similarity_threshold=embeddings_data.get('similarity_threshold', 0.7),
            auto_create_collections=embeddings_data.get('auto_create_collections', True),
            default_collection_name=embeddings_data.get('default_collection_name', 'documents'),
            persist_directory=embeddings_data.get('persist_directory')
        )
        
        return cls(
            ollama_server=ollama_server,
            ui_preferences=ui_preferences,
            chat_defaults=chat_defaults,
            embeddings=embeddings,
            data_directory=data.get('data_directory'),
            cache_directory=data.get('cache_directory'),
            logs_directory=data.get('logs_directory'),
            database_file=data.get('database_file'),
            cache_expiry_hours=data.get('cache_expiry_hours', 24),
            log_level=data.get('log_level', 'INFO'),
            log_to_file=data.get('log_to_file', True),
            max_log_size_mb=data.get('max_log_size_mb', 10),
            log_backup_count=data.get('log_backup_count', 5),
            first_run=data.get('first_run', True),
            last_model_refresh=data.get('last_model_refresh')
        )

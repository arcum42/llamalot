"""
Backend module for LlamaLot application.

Contains the Ollama client, database manager, cache manager, and related utilities.
"""

from .ollama_client import OllamaClient
from .database import DatabaseManager, MigrationError
from .cache import CacheManager
from .exceptions import (
    LlamaLotError,
    OllamaConnectionError,
    ModelNotFoundError,
    ModelDownloadError,
    DatabaseError,
    MigrationError,
    CacheError,
    ConfigurationError,
    ChatError
)

__all__ = [
    'OllamaClient',
    'DatabaseManager', 
    'CacheManager',
    'LlamaLotError',
    'OllamaConnectionError',
    'ModelNotFoundError',
    'ModelDownloadError',
    'DatabaseError',
    'MigrationError',
    'CacheError',
    'ConfigurationError',
    'ChatError'
]

from .config import ConfigurationManager, get_config_manager, get_config
from .database import DatabaseManager, get_database_manager, DatabaseError, MigrationError
from .cache import CacheManager, get_cache_manager

# Import exceptions for convenience
from .ollama_client import OllamaClient, OllamaConnectionError, OllamaModelNotFoundError

__all__ = [
    'ConfigurationManager',
    'get_config_manager', 
    'get_config',
    'DatabaseManager',
    'get_database_manager',
    'DatabaseError',
    'MigrationError',
    'CacheManager',
    'get_cache_manager',
    'OllamaClient',
    'OllamaConnectionError',
    'OllamaModelNotFoundError',
]

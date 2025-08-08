"""
Backend module for LlamaLot application.

Contains the Ollama client, database manager, cache manager, embeddings manager, and related utilities.
"""

from .ollama_client import OllamaClient, OllamaConnectionError, OllamaModelNotFoundError
from .database import DatabaseManager, get_database_manager, DatabaseError, MigrationError
from .cache import CacheManager, get_cache_manager
from .config import ConfigurationManager, get_config_manager, get_config
from .embeddings_manager import EmbeddingsManager, Document, SearchResult
from .exceptions import (
    LlamaLotError,
    OllamaConnectionError,
    ModelNotFoundError,
    ModelDownloadError,
    DatabaseError,
    MigrationError,
    CacheError,
    ConfigurationError,
    ChatError,
    EmbeddingsError,
    VectorDatabaseError
)

__all__ = [
    'OllamaClient',
    'OllamaConnectionError',
    'OllamaModelNotFoundError',
    'DatabaseManager', 
    'get_database_manager',
    'DatabaseError',
    'MigrationError',
    'CacheManager',
    'get_cache_manager',
    'ConfigurationManager',
    'get_config_manager', 
    'get_config',
    'EmbeddingsManager',
    'Document',
    'SearchResult',
    'LlamaLotError',
    'ModelNotFoundError',
    'ModelDownloadError',
    'CacheError',
    'ConfigurationError',
    'ChatError',
    'EmbeddingsError',
    'VectorDatabaseError'
]

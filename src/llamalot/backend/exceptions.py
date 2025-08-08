"""
Exception classes for LlamaLot backend operations.

Provides custom exception types for different error conditions
in Ollama client, database, and cache operations.
"""


class LlamaLotError(Exception):
    """Base exception class for LlamaLot application errors."""
    pass


class OllamaConnectionError(LlamaLotError):
    """Raised when unable to connect to Ollama server."""
    pass


class ModelNotFoundError(LlamaLotError):
    """Raised when a requested model is not found."""
    pass


class ModelDownloadError(LlamaLotError):
    """Raised when model download fails."""
    pass


class DatabaseError(LlamaLotError):
    """Base class for database-related errors."""
    pass


class MigrationError(DatabaseError):
    """Raised when database migration fails."""
    pass


class CacheError(LlamaLotError):
    """Raised when cache operations fail."""
    pass


class ConfigurationError(LlamaLotError):
    """Raised when configuration is invalid or missing."""
    pass


class ChatError(LlamaLotError):
    """Raised when chat operations fail."""
    pass

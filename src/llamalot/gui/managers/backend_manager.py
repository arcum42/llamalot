"""
Backend components manager for LlamaLot application.

Centralizes initialization and management of all backend services
including Ollama client, database, and cache.
"""

from typing import Optional
from pathlib import Path

from llamalot.utils.logging_config import get_logger
from llamalot.backend.ollama_client import OllamaClient
from llamalot.backend.cache import CacheManager
from llamalot.backend.database import DatabaseManager
from llamalot.models.config import ApplicationConfig

logger = get_logger(__name__)


class BackendManager:
    """Manages all backend components for the LlamaLot application."""
    
    def __init__(self):
        """Initialize the backend manager."""
        self.config: Optional[ApplicationConfig] = None
        self.ollama_client: Optional[OllamaClient] = None
        self.cache_manager: Optional[CacheManager] = None
        self.db_manager: Optional[DatabaseManager] = None
        
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize all backend components."""
        if self._initialized:
            return True
            
        try:
            # Load configuration
            self.config = ApplicationConfig.load_from_file()
            self.config.ensure_directories()
            logger.info("Configuration loaded")
            
            # Initialize database
            db_path = Path(self.config.database_file or "llamalot.db")
            self.db_manager = DatabaseManager(db_path)
            logger.info(f"Database initialized: {db_path}")
            
            # Initialize Ollama client
            self.ollama_client = OllamaClient(self.config.ollama_server)
            logger.info(f"Ollama client initialized: {self.config.ollama_server}")
            
            # Initialize cache manager
            self.cache_manager = CacheManager(
                self.db_manager,
                self.ollama_client
            )
            logger.info("Cache manager initialized")
            
            self._initialized = True
            logger.info("All backend components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize backend components: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up all backend resources."""
        try:
            if self.db_manager:
                self.db_manager.close()
                logger.info("Database connections closed")
            
            if self.config:
                self.config.save_to_file()
                logger.info("Configuration saved")
                
            self._initialized = False
            logger.info("Backend cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during backend cleanup: {e}")
    
    def is_initialized(self) -> bool:
        """Check if backend is fully initialized."""
        return self._initialized

"""
Configuration management for LlamaLot application.

Handles loading, saving, and managing application configuration.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json

from llamalot.models import ApplicationConfig
from llamalot.utils.logging_config import get_logger

logger = get_logger(__name__)


class ConfigurationManager:
    """
    Manages application configuration with automatic loading and saving.
    
    This class provides a centralized way to access and modify application
    settings, with automatic persistence to disk.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Custom path to config file (optional)
        """
        self.config_path = config_path or ApplicationConfig.get_config_file_path()
        self._config: Optional[ApplicationConfig] = None
        self._loaded = False
        
        logger.info(f"Configuration manager initialized with path: {self.config_path}")
    
    @property
    def config(self) -> ApplicationConfig:
        """
        Get the current application configuration.
        
        Loads from file if not already loaded.
        
        Returns:
            ApplicationConfig instance
        """
        if not self._loaded:
            self.load()
        assert self._config is not None
        return self._config
    
    def load(self) -> ApplicationConfig:
        """
        Load configuration from file.
        
        Returns:
            Loaded ApplicationConfig instance
        """
        try:
            logger.debug(f"Loading configuration from {self.config_path}")
            self._config = ApplicationConfig.load_from_file(self.config_path)
            self._loaded = True
            
            # Ensure directories exist
            self._config.ensure_directories()
            
            logger.info("Configuration loaded successfully")
            return self._config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Fall back to default configuration
            self._config = ApplicationConfig()
            self._config.ensure_directories()
            self._loaded = True
            return self._config
    
    def save(self) -> bool:
        """
        Save current configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        if not self._loaded or self._config is None:
            logger.warning("No configuration to save")
            return False
        
        try:
            logger.debug(f"Saving configuration to {self.config_path}")
            self._config.save_to_file(self.config_path)
            logger.info("Configuration saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def reset_to_defaults(self) -> ApplicationConfig:
        """
        Reset configuration to default values.
        
        Returns:
            New default ApplicationConfig instance
        """
        logger.info("Resetting configuration to defaults")
        self._config = ApplicationConfig()
        self._config.ensure_directories()
        self._loaded = True
        return self._config
    
    def update_ollama_server(self, host: str, port: int, use_https: bool = False, timeout: int = 180) -> None:
        """
        Update Ollama server configuration.
        
        Args:
            host: Server hostname
            port: Server port
            use_https: Whether to use HTTPS
            timeout: Connection timeout in seconds
        """
        config = self.config
        config.ollama_server.host = host
        config.ollama_server.port = port
        config.ollama_server.use_https = use_https
        config.ollama_server.timeout = timeout
        
        logger.info(f"Updated Ollama server config: {config.ollama_server.base_url}")
    
    def update_ui_preferences(self, **kwargs) -> None:
        """
        Update UI preferences.
        
        Args:
            **kwargs: UI preference fields to update
        """
        config = self.config
        ui_prefs = config.ui_preferences
        
        # Update provided fields
        for key, value in kwargs.items():
            if hasattr(ui_prefs, key):
                setattr(ui_prefs, key, value)
                logger.debug(f"Updated UI preference {key} = {value}")
            else:
                logger.warning(f"Unknown UI preference: {key}")
    
    def update_chat_defaults(self, **kwargs) -> None:
        """
        Update chat default settings.
        
        Args:
            **kwargs: Chat default fields to update
        """
        config = self.config
        chat_defaults = config.chat_defaults
        
        # Update provided fields
        for key, value in kwargs.items():
            if hasattr(chat_defaults, key):
                setattr(chat_defaults, key, value)
                logger.debug(f"Updated chat default {key} = {value}")
            else:
                logger.warning(f"Unknown chat default: {key}")
    
    def update_embeddings_config(self, **kwargs) -> None:
        """
        Update embeddings configuration settings.
        
        Args:
            **kwargs: Embeddings config fields to update
        """
        config = self.config
        embeddings_config = config.embeddings
        
        # Update provided fields
        for key, value in kwargs.items():
            if hasattr(embeddings_config, key):
                setattr(embeddings_config, key, value)
                logger.debug(f"Updated embeddings config {key} = {value}")
            else:
                logger.warning(f"Unknown embeddings config: {key}")
    
    def mark_first_run_complete(self) -> None:
        """Mark that the first run setup is complete."""
        config = self.config
        config.first_run = False
        logger.info("Marked first run as complete")
    
    def update_last_model_refresh(self) -> None:
        """Update the timestamp of the last model refresh."""
        from datetime import datetime
        config = self.config
        config.last_model_refresh = datetime.now().isoformat()
        logger.debug("Updated last model refresh timestamp")
    
    def get_data_directory(self) -> Path:
        """
        Get the application data directory.
        
        Returns:
            Path to data directory
        """
        data_dir = self.config.data_directory
        if data_dir is None:
            raise ValueError("Data directory not configured")
        return Path(data_dir)
    
    def get_cache_directory(self) -> Path:
        """
        Get the cache directory.
        
        Returns:
            Path to cache directory
        """
        cache_dir = self.config.cache_directory
        if cache_dir is None:
            raise ValueError("Cache directory not configured")
        return Path(cache_dir)
    
    def get_logs_directory(self) -> Path:
        """
        Get the logs directory.
        
        Returns:
            Path to logs directory
        """
        logs_dir = self.config.logs_directory
        if logs_dir is None:
            raise ValueError("Logs directory not configured")
        return Path(logs_dir)
    
    def get_database_path(self) -> Path:
        """
        Get the database file path.
        
        Returns:
            Path to database file
        """
        db_file = self.config.database_file
        if db_file is None:
            raise ValueError("Database file not configured")
        return Path(db_file)
    
    def export_config(self, export_path: Path) -> bool:
        """
        Export configuration to a file.
        
        Args:
            export_path: Path to export the configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            config_dict = self.config.to_dict()
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration exported to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_config(self, import_path: Path) -> bool:
        """
        Import configuration from a file.
        
        Args:
            import_path: Path to import the configuration from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            self._config = ApplicationConfig.from_dict(config_dict)
            self._config.ensure_directories()
            self._loaded = True
            
            logger.info(f"Configuration imported from {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate the current configuration.
        
        Returns:
            Dictionary with validation results
        """
        config = self.config
        results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check data directories
        try:
            data_dir_str = config.data_directory
            if data_dir_str is None:
                results['errors'].append("Data directory is not configured")
                results['valid'] = False
            else:
                data_dir = Path(data_dir_str)
                if not data_dir.exists():
                    results['warnings'].append(f"Data directory does not exist: {data_dir}")
        except Exception as e:
            results['errors'].append(f"Invalid data directory path: {e}")
            results['valid'] = False
        
        # Check Ollama server configuration
        if not config.ollama_server.host:
            results['errors'].append("Ollama server host is empty")
            results['valid'] = False
        
        if not (1 <= config.ollama_server.port <= 65535):
            results['errors'].append(f"Invalid Ollama server port: {config.ollama_server.port}")
            results['valid'] = False
        
        # Check UI preferences
        if config.ui_preferences.window_width < 100:
            results['warnings'].append("Window width is very small")
        
        if config.ui_preferences.window_height < 100:
            results['warnings'].append("Window height is very small")
        
        # Check chat defaults
        if not (0.0 <= config.chat_defaults.temperature <= 2.0):
            results['warnings'].append(f"Temperature outside normal range: {config.chat_defaults.temperature}")
        
        if not (0.0 <= config.chat_defaults.top_p <= 1.0):
            results['warnings'].append(f"Top-p outside valid range: {config.chat_defaults.top_p}")
        
        # Check embeddings configuration
        if config.embeddings.chunk_size < 100:
            results['warnings'].append("Embeddings chunk size is very small")
        
        if config.embeddings.chunk_size > 10000:
            results['warnings'].append("Embeddings chunk size is very large")
        
        if not (0.0 <= config.embeddings.similarity_threshold <= 1.0):
            results['warnings'].append(f"Similarity threshold outside valid range: {config.embeddings.similarity_threshold}")
        
        if config.embeddings.search_results_limit < 1:
            results['warnings'].append("Search results limit should be at least 1")
        
        # Check embeddings persist directory
        if config.embeddings.persist_directory:
            persist_dir = Path(config.embeddings.persist_directory)
            if not persist_dir.exists():
                results['warnings'].append(f"Embeddings persist directory does not exist: {persist_dir}")
        
        logger.debug(f"Configuration validation: {len(results['errors'])} errors, {len(results['warnings'])} warnings")
        return results
    
    def __str__(self) -> str:
        """String representation."""
        return f"ConfigurationManager(config_path={self.config_path}, loaded={self._loaded})"


# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> ConfigurationManager:
    """
    Get the global configuration manager instance.
    
    Returns:
        ConfigurationManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def get_config() -> ApplicationConfig:
    """
    Get the current application configuration.
    
    Returns:
        ApplicationConfig instance
    """
    return get_config_manager().config

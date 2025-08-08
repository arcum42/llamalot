"""
Cache manager for LlamaLot application.

Provides high-level caching functionality that integrates the database
with the Ollama client for intelligent model and conversation management.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Callable

from llamalot.backend.database import DatabaseManager, get_database_manager
from llamalot.backend.ollama_client import OllamaClient, OllamaConnectionError
from llamalot.backend.config import get_config
from llamalot.models import OllamaModel, ChatConversation
from llamalot.utils.logging_config import get_logger

logger = get_logger(__name__)


class CacheManager:
    """
    High-level cache manager that coordinates between database and API.
    
    Provides intelligent caching of models, conversations, and automatic
    synchronization with the Ollama server.
    """
    
    def __init__(
        self, 
        database_manager: Optional[DatabaseManager] = None,
        ollama_client: Optional[OllamaClient] = None
    ):
        """
        Initialize the cache manager.
        
        Args:
            database_manager: Optional DatabaseManager instance
            ollama_client: Optional OllamaClient instance
        """
        self.db = database_manager or get_database_manager()
        self.ollama = ollama_client
        self.config = get_config()
        
        # Cache configuration
        self.model_cache_ttl = timedelta(hours=1)  # Model list cache TTL
        self.auto_sync = True  # Automatically sync with Ollama
        
        logger.info("Cache manager initialized")
    
    def set_ollama_client(self, client: OllamaClient) -> None:
        """Set the Ollama client for API operations."""
        self.ollama = client
        logger.debug("Ollama client set for cache manager")
    
    # Model caching methods
    def get_models(self, force_refresh: bool = False) -> List[OllamaModel]:
        """
        Get list of models with intelligent caching.
        
        Args:
            force_refresh: Force refresh from Ollama server
            
        Returns:
            List of OllamaModel instances
        """
        # Check if we need to refresh from server
        should_refresh = force_refresh or self._should_refresh_models()
        
        if should_refresh and self.ollama:
            try:
                logger.info("Refreshing models from Ollama server")
                
                if force_refresh:
                    # For force refresh, use the full list_models() method which includes capabilities
                    logger.info("Force refresh - getting full model details from server")
                    server_models = self.ollama.list_models()
                    
                    # Update cache with all models
                    for model in server_models:
                        self.db.save_model(model)
                    
                    # Update last refresh timestamp
                    self.db.set_app_state('last_model_refresh', datetime.now().isoformat())
                    
                    logger.info(f"Successfully force-refreshed {len(server_models)} models from server")
                    return server_models
                else:
                    # For automatic refresh, use smart caching to minimize API calls
                    logger.info("Auto refresh - using smart caching")
                    
                    # Get basic model list from server
                    server_models = self.ollama.list_models_basic()
                    
                    # Get cached models to check what needs detailed fetching
                    cached_models = {model.name: model for model in self.db.list_models()}
                    
                    updated_models = []
                    for server_model in server_models:
                        cached_model = cached_models.get(server_model.name)
                        
                        # Check if we need to fetch detailed info
                        needs_details = (
                            not cached_model or  # Not in cache
                            not cached_model.capabilities or  # No capabilities cached
                            not cached_model.model_info or  # No model info cached
                            cached_model.digest != server_model.digest  # Different version
                        )
                        
                        if needs_details:
                            try:
                                logger.debug(f"Fetching detailed info for model: {server_model.name}")
                                # Get detailed model info including capabilities
                                detailed_model = self.ollama.get_model_info(server_model.name)
                                updated_models.append(detailed_model)
                            except Exception as e:
                                logger.warning(f"Failed to get detailed info for {server_model.name}: {e}")
                                # Use the cached model or fallback to server model
                                updated_models.append(cached_model if cached_model else server_model)
                        else:
                            # Use cached model with updated basic info from server
                            if cached_model:
                                cached_model.size = server_model.size
                                cached_model.digest = server_model.digest
                                cached_model.modified_at = server_model.modified_at
                                updated_models.append(cached_model)
                            else:
                                # Shouldn't happen, but add server model as fallback
                                updated_models.append(server_model)
                    
                    # Update cache with all models
                    for model in updated_models:
                        self.db.save_model(model)
                    
                    # Update last refresh timestamp
                    self.db.set_app_state('last_model_refresh', datetime.now().isoformat())
                    
                    logger.info(f"Successfully refreshed {len(updated_models)} models from server")
                    return updated_models
                
            except OllamaConnectionError as e:
                logger.warning(f"Failed to refresh models from server: {e}")
                # Fall back to cached models
        
        # Return cached models
        cached_models = self.db.list_models()
        logger.debug(f"Retrieved {len(cached_models)} models from cache")
        return cached_models
    
    def get_model(self, name: str, fetch_details: bool = True) -> Optional[OllamaModel]:
        """
        Get a specific model with caching.
        
        Args:
            name: Model name
            fetch_details: Whether to fetch detailed model info
            
        Returns:
            OllamaModel instance or None if not found
        """
        # Try cache first
        model = self.db.get_model(name)
        
        # If not in cache or details missing, try to fetch from server
        if (not model or (fetch_details and not model.model_info)) and self.ollama:
            try:
                # Get basic model info
                if not model:
                    server_models = self.ollama.list_models()
                    model = next((m for m in server_models if m.name == name), None)
                
                # Get detailed model info if requested
                if model and fetch_details and not model.model_info:
                    logger.debug(f"Fetching detailed info for model: {name}")
                    detailed_model = self.ollama.get_model_info(name)
                    # Replace with the detailed model which includes model_info
                    model = detailed_model
                
                # Save to cache
                if model:
                    self.db.save_model(model)
                
            except OllamaConnectionError as e:
                logger.warning(f"Failed to fetch model {name} from server: {e}")
        
        return model
    
    def refresh_model(self, name: str) -> Optional[OllamaModel]:
        """
        Force refresh a specific model from the server.
        
        Args:
            name: Model name
            
        Returns:
            Updated OllamaModel instance or None
        """
        if not self.ollama:
            logger.warning("No Ollama client available for model refresh")
            return None
        
        try:
            logger.info(f"Force refreshing model: {name}")
            
            # Get fresh detailed model info from server
            model = self.ollama.get_model_info(name)
            
            if model:
                # Update cache
                self.db.save_model(model)
                logger.debug(f"Refreshed and cached model: {name}")
            
            return model
            
        except OllamaConnectionError as e:
            logger.error(f"Failed to refresh model {name}: {e}")
            return None
    
    def delete_model_cache(self, name: str) -> bool:
        """
        Delete a model from the cache.
        
        Args:
            name: Model name
            
        Returns:
            True if deleted, False if not found
        """
        deleted = self.db.delete_model(name)
        if deleted:
            logger.debug(f"Deleted model from cache: {name}")
        return deleted
    
    def _should_refresh_models(self) -> bool:
        """Check if models should be refreshed from server."""
        if not self.auto_sync:
            return False
        
        last_refresh = self.db.get_app_state('last_model_refresh')
        if not last_refresh:
            return True
        
        try:
            last_refresh_time = datetime.fromisoformat(last_refresh)
            return datetime.now() - last_refresh_time > self.model_cache_ttl
        except (ValueError, TypeError):
            return True
    
    # Conversation caching methods
    def save_conversation(self, conversation: ChatConversation) -> None:
        """
        Save a conversation to the cache.
        
        Args:
            conversation: ChatConversation to save
        """
        self.db.save_conversation(conversation)
        logger.debug(f"Saved conversation to cache: {conversation.conversation_id}")
    
    def get_conversation(self, conversation_id: str) -> Optional[ChatConversation]:
        """
        Get a conversation from the cache.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            ChatConversation instance or None if not found
        """
        conversation = self.db.get_conversation(conversation_id)
        if conversation:
            logger.debug(f"Retrieved conversation from cache: {conversation_id}")
        return conversation
    
    def list_conversations(
        self, 
        model_filter: Optional[str] = None, 
        limit: Optional[int] = None
    ) -> List[tuple]:
        """
        List conversations from the cache.
        
        Args:
            model_filter: Optional model name filter
            limit: Optional limit on results
            
        Returns:
            List of tuples: (conversation_id, title, updated_at)
        """
        conversations = self.db.list_conversations(model_filter, limit)
        logger.debug(f"Listed {len(conversations)} conversations from cache")
        return conversations
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation from the cache.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if deleted, False if not found
        """
        deleted = self.db.delete_conversation(conversation_id)
        if deleted:
            logger.debug(f"Deleted conversation from cache: {conversation_id}")
        return deleted
    
    # Application state methods
    def get_app_setting(self, key: str, default: Any = None) -> Any:
        """
        Get an application setting from the cache.
        
        Args:
            key: Setting key
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        return self.db.get_app_state(key, default)
    
    def set_app_setting(self, key: str, value: Any, description: Optional[str] = None) -> None:
        """
        Set an application setting in the cache.
        
        Args:
            key: Setting key
            value: Setting value
            description: Optional description
        """
        self.db.set_app_state(key, value, description)
    
    def delete_app_setting(self, key: str) -> bool:
        """
        Delete an application setting from the cache.
        
        Args:
            key: Setting key
            
        Returns:
            True if deleted, False if not found
        """
        return self.db.delete_app_state(key)
    
    # Synchronization methods
    def sync_with_server(
        self, 
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, Any]:
        """
        Synchronize cache with Ollama server.
        
        Args:
            progress_callback: Optional progress callback function
            
        Returns:
            Synchronization results
        """
        if not self.ollama:
            raise ValueError("No Ollama client available for synchronization")
        
        results = {
            'models_updated': 0,
            'models_removed': 0,
            'errors': []
        }
        
        try:
            if progress_callback:
                progress_callback("Fetching server models...", 0.1)
            
            # Get models from server
            server_models = self.ollama.list_models()
            server_model_names = {model.name for model in server_models}
            
            if progress_callback:
                progress_callback("Fetching cached models...", 0.2)
            
            # Get cached models
            cached_models = self.db.list_models()
            cached_model_names = {model.name for model in cached_models}
            
            # Update/add models from server
            total_models = len(server_models)
            for i, model in enumerate(server_models):
                try:
                    if progress_callback:
                        progress = 0.2 + (0.6 * i / total_models)
                        progress_callback(f"Updating model: {model.name}", progress)
                    
                    # Get detailed info - this returns a complete model with all details
                    detailed_model = self.ollama.get_model_info(model.name)
                    
                    # Save the detailed model to cache
                    self.db.save_model(detailed_model)
                    results['models_updated'] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to update model {model.name}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            if progress_callback:
                progress_callback("Removing stale models...", 0.8)
            
            # Remove models that are no longer on server
            for cached_name in cached_model_names - server_model_names:
                try:
                    self.db.delete_model(cached_name)
                    results['models_removed'] += 1
                    logger.debug(f"Removed stale model from cache: {cached_name}")
                except Exception as e:
                    error_msg = f"Failed to remove model {cached_name}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            # Update sync timestamp
            self.db.set_app_state('last_model_refresh', datetime.now().isoformat())
            self.db.set_app_state('last_full_sync', datetime.now().isoformat())
            
            if progress_callback:
                progress_callback("Synchronization complete", 1.0)
            
            logger.info(f"Synchronization completed: {results}")
            
        except Exception as e:
            error_msg = f"Synchronization failed: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            raise
        
        return results
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get synchronization status information.
        
        Returns:
            Dictionary with sync status
        """
        last_refresh = self.db.get_app_state('last_model_refresh')
        last_full_sync = self.db.get_app_state('last_full_sync')
        
        status = {
            'last_refresh': last_refresh,
            'last_full_sync': last_full_sync,
            'needs_refresh': self._should_refresh_models(),
            'auto_sync_enabled': self.auto_sync,
            'cache_ttl_hours': self.model_cache_ttl.total_seconds() / 3600
        }
        
        if last_refresh:
            try:
                last_refresh_time = datetime.fromisoformat(last_refresh)
                status['refresh_age_minutes'] = (datetime.now() - last_refresh_time).total_seconds() / 60
            except (ValueError, TypeError):
                status['refresh_age_minutes'] = None
        
        return status
    
    # Maintenance methods
    def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """
        Clean up old cached data.
        
        Args:
            days: Number of days to keep data
            
        Returns:
            Cleanup statistics
        """
        logger.info(f"Cleaning up data older than {days} days")
        stats = self.db.cleanup_old_data(days)
        logger.info(f"Cleanup completed: {stats}")
        return stats
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        db_stats = self.db.get_database_stats()
        
        # Add cache-specific stats
        stats = {
            **db_stats,
            'auto_sync': self.auto_sync,
            'cache_ttl_hours': self.model_cache_ttl.total_seconds() / 3600,
            'has_ollama_client': self.ollama is not None
        }
        
        return stats
    
    def reset_cache(self) -> None:
        """Reset all cached data."""
        logger.warning("Resetting all cached data")
        
        # Clear all models and conversations
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM models")
            conn.execute("DELETE FROM conversations")
            conn.execute("DELETE FROM messages")
            conn.execute("DELETE FROM message_attachments")
        
        # Reset sync timestamps
        self.db.delete_app_state('last_model_refresh')
        self.db.delete_app_state('last_full_sync')
        
        logger.info("Cache reset completed")
    
    # Configuration methods
    def configure(
        self, 
        auto_sync: Optional[bool] = None,
        cache_ttl_hours: Optional[float] = None
    ) -> None:
        """
        Configure cache behavior.
        
        Args:
            auto_sync: Enable/disable automatic synchronization
            cache_ttl_hours: Cache TTL in hours
        """
        if auto_sync is not None:
            self.auto_sync = auto_sync
            self.db.set_app_state('cache_auto_sync', auto_sync)
            logger.info(f"Auto-sync {'enabled' if auto_sync else 'disabled'}")
        
        if cache_ttl_hours is not None:
            self.model_cache_ttl = timedelta(hours=cache_ttl_hours)
            self.db.set_app_state('cache_ttl_hours', cache_ttl_hours)
            logger.info(f"Cache TTL set to {cache_ttl_hours} hours")
    
    def load_configuration(self) -> None:
        """Load cache configuration from database."""
        auto_sync = self.db.get_app_state('cache_auto_sync', True)
        cache_ttl_hours = self.db.get_app_state('cache_ttl_hours', 1.0)
        
        self.auto_sync = auto_sync
        self.model_cache_ttl = timedelta(hours=cache_ttl_hours)
        
        logger.debug(f"Loaded cache configuration: auto_sync={auto_sync}, ttl={cache_ttl_hours}h")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Cache manager doesn't need explicit cleanup
        pass


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    Get the global cache manager instance.
    
    Returns:
        CacheManager instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
        _cache_manager.load_configuration()
    return _cache_manager

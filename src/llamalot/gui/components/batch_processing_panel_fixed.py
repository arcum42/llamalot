"""
Batch image processing panel component.

Allows users to select a vision model, enter a prompt, attach multiple images,
and process them in batch to generate text descriptions saved alongside each image.
"""

import wx
import os
import threading
import asyncio
from typing import List, Optional, Callable
from pathlib import Path

from llamalot.models.chat import ChatImage
from llamalot.models.ollama_model import OllamaModel
from llamalot.backend.ollama_client import OllamaClient
from llamalot.utils.logging_config import get_logger

logger = get_logger(__name__)


class BatchProcessingPanel(wx.Panel):
    """
    Panel for batch processing images with vision models.
    
    Features:
    - Vision model selection dropdown
    - Prompt input text field
    - Image attachment panel
    - Batch processing with progress indication
    - Automatic text file generation next to images
    """
    
    def __init__(self, parent: wx.Window, ollama_client, cache_manager, on_status_update: Optional[Callable[[str], None]] = None):
        """
        Initialize the batch processing panel.
        
        Args:
            parent: Parent window/panel
            ollama_client: OllamaClient instance for API calls
            cache_manager: CacheManager instance for cached model data
            on_status_update: Optional callback for status updates
        """
        super().__init__(parent)
        
        self.ollama_client = ollama_client
        self.cache_manager = cache_manager
        self.on_status_update = on_status_update
        self.vision_models: List[OllamaModel] = []
        self.selected_model: Optional[OllamaModel] = None
        self.attached_images: List[ChatImage] = []
        self.selected_images: List[ChatImage] = []  # Track selected images
        self.image_panels: List[wx.Panel] = []  # Track image panel widgets
        self.is_processing = False
        
        self._create_ui()
        self._bind_events()
        self._load_vision_models()
        
    def _load_vision_models(self) -> None:
        """Load available vision models."""
        try:
            # Use cache manager instead of direct ollama client for better performance
            all_models = self.cache_manager.get_models(force_refresh=False)
            self.vision_models = [model for model in all_models if 'vision' in model.capabilities]
            
            # Update choice control
            model_names = [model.name for model in self.vision_models]
            self.model_choice.SetItems(model_names)
            
            if self.vision_models:
                self.model_choice.SetSelection(0)
                self.selected_model = self.vision_models[0]
            
            self._update_process_button_state()
            logger.info(f"Loaded {len(self.vision_models)} vision models for batch processing")
            
        except Exception as e:
            logger.error(f"Error loading vision models: {e}")
            self._update_status(f"Error loading models: {e}", error=True)

"""
Batch Tab for LlamaLot GUI.

Provides batch processing functionality using the BatchProcessingPanel component.
"""

import wx
import logging
from llamalot.utils.logging_config import get_logger
from llamalot.gui.components.batch_processing_panel import BatchProcessingPanel

logger = get_logger(__name__)


class BatchTab:
    """Batch tab component for batch processing functionality."""
    
    def __init__(self, parent_notebook, ollama_client, cache_manager, main_window_ref=None):
        """Initialize the batch tab."""
        self.notebook = parent_notebook
        self.ollama_client = ollama_client
        self.cache_manager = cache_manager
        self.main_window = main_window_ref  # Reference to main window for status updates
        
        # Create the tab and add to notebook
        self.create_batch_tab()
        
    def create_batch_tab(self) -> None:
        """Create the batch processing tab."""
        # Create batch processing panel
        self.batch_panel = BatchProcessingPanel(
            self.notebook,
            self.ollama_client,
            self.cache_manager,
            on_status_update=self.on_batch_status_update
        )
        
        # Add tab to notebook
        self.notebook.AddPage(self.batch_panel, "🔄 Batch Processing", False)
        
    def on_batch_status_update(self, message: str) -> None:
        """Handle status updates from batch processing."""
        try:
            # Update status bar via main window reference
            if self.main_window and hasattr(self.main_window, 'status_bar'):
                self.main_window.status_bar.SetStatusText(f"Batch: {message}", 1)
        except Exception as e:
            logger.error(f"Error updating batch status: {e}")

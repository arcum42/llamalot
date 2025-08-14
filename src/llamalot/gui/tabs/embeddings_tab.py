"""
Embeddings Tab for LlamaLot GUI.

Provides embeddings management functionality using the EmbeddingsPanel component.
"""

import wx
import logging
from typing import List
from llamalot.utils.logging_config import get_logger
from llamalot.gui.components.embeddings_panel import EmbeddingsPanel

logger = get_logger(__name__)


class EmbeddingsTab(wx.Panel):
    """Embeddings tab component for managing embeddings and RAG functionality."""
    
    def __init__(self, parent_notebook, main_window_ref=None):
        """Initialize the embeddings tab."""
        super().__init__(parent_notebook)
        
        self.notebook = parent_notebook
        self.main_window = main_window_ref  # Reference to main window for status updates
        
        # Create the tab content
        self.create_embeddings_tab()
        
    def create_embeddings_tab(self) -> None:
        """Create the embeddings management tab."""
        # Create a sizer for the tab
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create the embeddings panel using our comprehensive EmbeddingsPanel component
        try:
            self.embeddings_panel = EmbeddingsPanel(self)
            
            # Add panel to the sizer
            sizer.Add(self.embeddings_panel, 1, wx.EXPAND | wx.ALL, 5)
            
            # Bind events for chat integration
            self.embeddings_panel.Bind(wx.EVT_MENU, self.on_embeddings_settings_changed)
            
            logger.info("Embeddings tab created successfully")
            
        except Exception as e:
            logger.error(f"Error creating embeddings tab: {e}")
            # Create a simple placeholder panel if EmbeddingsPanel fails
            error_text = wx.StaticText(
                self, 
                label=f"Embeddings functionality unavailable: {e}\nPlease check your configuration."
            )
            sizer.Add(error_text, 1, wx.EXPAND | wx.ALL, 20)
            self.embeddings_panel = None  # Mark as unavailable
        
        self.SetSizer(sizer)
    
    def on_embeddings_settings_changed(self, event):
        """Handle embeddings settings changes for chat integration."""
        try:
            if hasattr(self, 'embeddings_panel') and self.embeddings_panel and hasattr(self.embeddings_panel, 'is_rag_enabled'):
                # Update chat interface based on embeddings settings
                rag_enabled = self.embeddings_panel.is_rag_enabled()
                active_collections = self.embeddings_panel.get_active_collections()
                
                logger.info(f"Embeddings settings changed - RAG enabled: {rag_enabled}, Active collections: {len(active_collections)}")
                
                # Update status bar via main window reference
                if self.main_window and hasattr(self.main_window, 'status_bar'):
                    if rag_enabled and active_collections:
                        self.main_window.status_bar.SetStatusText(f"RAG enabled ({len(active_collections)} collections)", 1)
                    else:
                        self.main_window.status_bar.SetStatusText("RAG disabled", 1)
                    
        except Exception as e:
            logger.error(f"Error handling embeddings settings change: {e}")
    
    def get_embeddings_context(self, query: str, max_results: int = 3) -> List:
        """
        Get embeddings context for chat integration.
        
        Args:
            query: The user's query to search for relevant context
            max_results: Maximum number of context results to return
            
        Returns:
            List of relevant document excerpts for context
        """
        try:
            if hasattr(self, 'embeddings_panel') and self.embeddings_panel:
                return self.embeddings_panel.search_for_context(query, max_results)
            return []
        except Exception as e:
            logger.error(f"Error getting embeddings context: {e}")
            return []

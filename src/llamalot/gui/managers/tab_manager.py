"""
Tab manager for LlamaLot application.

Handles creation and management of application tabs including
models, chat, history, embeddings, and batch processing.
"""

import wx
from typing import Optional, Dict, Any

from llamalot.utils.logging_config import get_logger
from llamalot.gui.tabs.models_tab import ModelsTab
from llamalot.gui.tabs.chat_tab import ChatTab
from llamalot.gui.tabs.history_tab import HistoryTab
from llamalot.gui.tabs.embeddings_tab import EmbeddingsTab
from llamalot.gui.tabs.batch_tab import BatchTab

logger = get_logger(__name__)


class TabManager:
    """Manages all application tabs."""
    
    def __init__(self, parent_window: wx.Frame, notebook: wx.Notebook):
        """Initialize the tab manager."""
        self.parent = parent_window
        self.notebook = notebook
        
        # Tab instances (stored for reference)
        self.models_tab = None
        self.chat_tab = None
        self.history_tab = None
        self.embeddings_tab = None
        self.batch_tab = None
        
        # Backend components (to be set by parent)
        self.ollama_client = None
        self.cache_manager = None
        self.db_manager = None
        self.config = None
    
    def set_backend_components(self, ollama_client, cache_manager, db_manager, config) -> None:
        """Set the backend component references."""
        self.ollama_client = ollama_client
        self.cache_manager = cache_manager
        self.db_manager = db_manager
        self.config = config
    
    def create_all_tabs(self) -> None:
        """Create all application tabs."""
        if not all([self.ollama_client, self.cache_manager, self.db_manager, self.config]):
            logger.error("Backend components not set")
            return
            
        try:
            # Create tabs in order
            self._create_models_tab()
            self._create_chat_tab()
            self._create_batch_tab()
            self._create_embeddings_tab()
            self._create_history_tab()
            
            # Select the first tab
            if self.notebook.GetPageCount() > 0:
                self.notebook.SetSelection(0)
                
            logger.info(f"Created {self.notebook.GetPageCount()} tabs successfully")
            
        except Exception as e:
            logger.error(f"Failed to create tabs: {e}")
            wx.MessageBox(
                f"Failed to create application tabs:\\n{str(e)}", 
                "Tab Creation Error", 
                wx.OK | wx.ICON_ERROR
            )
    
    def _create_models_tab(self) -> None:
        """Create the models management tab."""
        try:
            self.models_tab = ModelsTab(self.notebook, self.parent)
            self.notebook.AddPage(self.models_tab, "🔧 Models")
            logger.info("Models tab created")
        except Exception as e:
            logger.error(f"Failed to create models tab: {e}")
            raise
    
    def _create_chat_tab(self) -> None:
        """Create the chat interface tab."""
        try:
            self.chat_tab = ChatTab(self.notebook, self.parent)
            self.notebook.AddPage(self.chat_tab, "💬 Chat")
            logger.info("Chat tab created")
        except Exception as e:
            logger.error(f"Failed to create chat tab: {e}")
            raise
    
    def _create_history_tab(self) -> None:
        """Create the conversation history tab."""
        try:
            self.history_tab = HistoryTab(self.notebook, self.db_manager, self.parent)
            logger.info("History tab created")
        except Exception as e:
            logger.error(f"Failed to create history tab: {e}")
            raise
    
    def _create_embeddings_tab(self) -> None:
        """Create the embeddings management tab."""
        try:
            self.embeddings_tab = EmbeddingsTab(self.notebook, self.parent)
            logger.info("Embeddings tab created")
        except Exception as e:
            logger.error(f"Failed to create embeddings tab: {e}")
            raise
    
    def _create_batch_tab(self) -> None:
        """Create the batch processing tab."""
        try:
            self.batch_tab = BatchTab(
                self.notebook, 
                self.ollama_client, 
                self.cache_manager, 
                self.parent
            )
            logger.info("Batch tab created")
        except Exception as e:
            logger.error(f"Failed to create batch tab: {e}")
            raise
    
    def get_tab_by_name(self, tab_name: str) -> Optional[wx.Panel]:
        """Get a tab instance by name."""
        tab_map = {
            'models': self.models_tab,
            'chat': self.chat_tab,
            'history': self.history_tab,
            'embeddings': self.embeddings_tab,
            'batch': self.batch_tab
        }
        return tab_map.get(tab_name)
    
    def refresh_tab(self, tab_name: str) -> None:
        """Refresh a specific tab."""
        tab = self.get_tab_by_name(tab_name)
        if tab and hasattr(tab, 'refresh'):
            try:
                tab.refresh()
                logger.info(f"Refreshed {tab_name} tab")
            except Exception as e:
                logger.error(f"Failed to refresh {tab_name} tab: {e}")
    
    def refresh_all_tabs(self) -> None:
        """Refresh all tabs."""
        for tab_name in ['models', 'chat', 'history', 'embeddings', 'batch']:
            self.refresh_tab(tab_name)
    
    def select_tab_by_index(self, index: int) -> bool:
        """Select a tab by index."""
        if 0 <= index < self.notebook.GetPageCount():
            self.notebook.SetSelection(index)
            return True
        return False
    
    def select_tab_by_title(self, title: str) -> bool:
        """Select a tab by title."""
        for i in range(self.notebook.GetPageCount()):
            if self.notebook.GetPageText(i) == title:
                self.notebook.SetSelection(i)
                return True
        return False
    
    def get_current_tab_index(self) -> int:
        """Get the index of the currently selected tab."""
        return self.notebook.GetSelection()
    
    def get_current_tab_title(self) -> str:
        """Get the title of the currently selected tab."""
        index = self.notebook.GetSelection()
        if index >= 0:
            return self.notebook.GetPageText(index)
        return ""
    
    def get_tab_count(self) -> int:
        """Get the number of tabs."""
        return self.notebook.GetPageCount()
    
    def on_tab_changed(self, event) -> None:
        """Handle tab selection change."""
        selection = event.GetSelection()
        if selection >= 0:
            tab_title = self.notebook.GetPageText(selection)
            logger.debug(f"Switched to tab: {tab_title}")
        event.Skip()
    
    def cleanup_tabs(self) -> None:
        """Clean up all tabs."""
        tabs = [self.models_tab, self.chat_tab, self.history_tab, 
                self.embeddings_tab, self.batch_tab]
        
        for tab in tabs:
            if tab and hasattr(tab, 'cleanup'):
                try:
                    tab.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up tab: {e}")
        
        # Clear references
        self.models_tab = None
        self.chat_tab = None
        self.history_tab = None
        self.embeddings_tab = None
        self.batch_tab = None

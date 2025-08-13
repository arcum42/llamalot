"""
Embeddings Chat Integration Panel for LlamaLot application.

Provides RAG (Retrieval Augmented Generation) controls for chat functionality,
including collection selection and RAG enable/disable toggle.
"""

import wx
import logging
from typing import List, Optional

from llamalot.backend import ConfigurationManager, EmbeddingsManager
from llamalot.backend.embeddings_manager import SearchResult
from llamalot.utils.logging_config import get_logger

logger = get_logger(__name__)


class EmbeddingsChatPanel(wx.Panel):
    """Panel for embeddings/RAG integration in chat tab."""
    
    def __init__(self, parent: wx.Window):
        """Initialize the embeddings chat panel."""
        super().__init__(parent)
        
        # Initialize backend
        self.config_manager = ConfigurationManager()
        self.embeddings_manager = EmbeddingsManager(self.config_manager)
        
        # State
        self.available_collections = []
        
        self._create_ui()
        self._bind_events()
        self._load_collections()
        self._load_settings()
        
        # Always show since parent collapsible pane handles visibility
        self.Show(True)
        
        logger.info("Embeddings chat panel initialized")
    
    def _create_ui(self) -> None:
        """Create the user interface."""
        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Header
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # RAG toggle checkbox
        self.rag_enabled_cb = wx.CheckBox(self, label="Enable RAG (Retrieval Augmented Generation)")
        self.rag_enabled_cb.SetToolTip("Use document embeddings to enhance chat responses with relevant context")
        header_sizer.Add(self.rag_enabled_cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        # Refresh collections button
        self.refresh_btn = wx.Button(self, label="Refresh", size=wx.Size(80, 25))
        self.refresh_btn.SetToolTip("Refresh available collections list")
        header_sizer.Add(self.refresh_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        main_sizer.Add(header_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Collections selection
        collections_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Label
        collections_sizer.Add(wx.StaticText(self, label="Active Collections:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        
        # Collections list (multiple selection)
        self.collections_listbox = wx.ListBox(self, style=wx.LB_MULTIPLE, size=wx.Size(-1, 60))
        self.collections_listbox.SetToolTip("Select collections to use for context retrieval")
        collections_sizer.Add(self.collections_listbox, 1, wx.EXPAND | wx.RIGHT, 5)
        
        # Status text
        self.status_text = wx.StaticText(self, label="Ready")
        self.status_text.SetFont(self.status_text.GetFont().Smaller())
        collections_sizer.Add(self.status_text, 0, wx.ALIGN_CENTER_VERTICAL)
        
        main_sizer.Add(collections_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(main_sizer)
        
        # Initially disable collections when RAG is disabled
        self._update_ui_state()
    
    def _bind_events(self) -> None:
        """Bind event handlers."""
        self.rag_enabled_cb.Bind(wx.EVT_CHECKBOX, self._on_rag_toggle)
        self.refresh_btn.Bind(wx.EVT_BUTTON, self._on_refresh)
        self.collections_listbox.Bind(wx.EVT_LISTBOX, self._on_collection_selection_changed)
    
    def _load_collections(self) -> None:
        """Load available collections from embeddings manager."""
        try:
            # Get available collections
            collections = self.embeddings_manager.list_collections()
            self.available_collections = collections
            
            # Update UI
            self.collections_listbox.Clear()
            for collection in collections:
                self.collections_listbox.Append(collection)
            
            # Update status
            count = len(collections)
            self.status_text.SetLabel(f"{count} collection{'s' if count != 1 else ''} available")
            
            logger.info(f"Loaded {count} collections for chat integration")
            
        except Exception as e:
            logger.error(f"Error loading collections: {e}")
            self.status_text.SetLabel("Error loading collections")
            self.available_collections = []
    
    def _load_settings(self) -> None:
        """Load RAG settings from configuration."""
        try:
            config = self.config_manager.config
            
            # Set RAG enabled state
            self.rag_enabled_cb.SetValue(config.embeddings.rag_enabled)
            
            # Set active collections
            active_collections = config.embeddings.active_collections or []
            for i, collection in enumerate(self.available_collections):
                if collection in active_collections:
                    self.collections_listbox.SetSelection(i)
            
            self._update_ui_state()
            
        except Exception as e:
            logger.error(f"Error loading RAG settings: {e}")
    
    def _save_settings(self) -> None:
        """Save current RAG settings to configuration."""
        try:
            config = self.config_manager.config
            
            # Save RAG enabled state
            config.embeddings.rag_enabled = self.rag_enabled_cb.GetValue()
            
            # Save active collections
            selected_indices = self.collections_listbox.GetSelections()
            active_collections = [self.available_collections[i] for i in selected_indices if i < len(self.available_collections)]
            config.embeddings.active_collections = active_collections
            
            # Save to file
            self.config_manager.save()
            
            logger.info(f"RAG settings saved: enabled={config.embeddings.rag_enabled}, collections={len(active_collections)}")
            
        except Exception as e:
            logger.error(f"Error saving RAG settings: {e}")
    
    def _update_ui_state(self) -> None:
        """Update UI state based on RAG enabled status."""
        rag_enabled = self.rag_enabled_cb.GetValue()
        self.collections_listbox.Enable(rag_enabled)
        
        if not rag_enabled:
            # Clear selection when disabled
            for i in range(self.collections_listbox.GetCount()):
                self.collections_listbox.Deselect(i)
    
    def _on_rag_toggle(self, event: wx.CommandEvent) -> None:
        """Handle RAG enable/disable toggle."""
        self._update_ui_state()
        self._save_settings()
        
        enabled = self.rag_enabled_cb.GetValue()
        logger.info(f"RAG {'enabled' if enabled else 'disabled'} for chat")
    
    def _on_refresh(self, event: wx.CommandEvent) -> None:
        """Handle refresh collections button."""
        self._load_collections()
        self._load_settings()  # Restore previous selection
    
    def _on_collection_selection_changed(self, event: wx.CommandEvent) -> None:
        """Handle collection selection change."""
        self._save_settings()
        
        selected_count = len(self.collections_listbox.GetSelections())
        logger.info(f"Selected {selected_count} collections for RAG")
    
    def show_panel(self, show: bool = True) -> None:
        """Show or hide the embeddings panel."""
        self.Show(show)
        if hasattr(self.GetParent(), 'Layout'):
            self.GetParent().Layout()
    
    def is_rag_enabled(self) -> bool:
        """Check if RAG is currently enabled."""
        return self.rag_enabled_cb.GetValue()
    
    def get_active_collections(self) -> List[str]:
        """Get list of currently active collections."""
        if not self.is_rag_enabled():
            return []
        
        selected_indices = self.collections_listbox.GetSelections()
        return [self.available_collections[i] for i in selected_indices if i < len(self.available_collections)]
    
    def search_for_context(self, query: str, max_results: int = 3) -> List[SearchResult]:
        """
        Search for context across active collections.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results for context
        """
        if not self.is_rag_enabled():
            return []
        
        active_collections = self.get_active_collections()
        if not active_collections:
            return []
        
        try:
            all_results = []
            for collection_name in active_collections:
                try:
                    results = self.embeddings_manager.search_similar(
                        collection_name, query, max_results
                    )
                    all_results.extend(results)
                except Exception as e:
                    logger.warning(f"Error searching collection {collection_name}: {e}")
                    continue
            
            # Sort by relevance score and limit results
            all_results.sort(key=lambda x: x.score, reverse=True)
            return all_results[:max_results]
            
        except Exception as e:
            logger.error(f"Error searching for context: {e}")
            return []
    
    def refresh_collections(self) -> None:
        """Public method to refresh collections list."""
        self._load_collections()
        self._load_settings()

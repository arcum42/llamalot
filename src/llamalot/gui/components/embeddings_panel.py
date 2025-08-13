"""
Embeddings Management Panel for LlamaLot application.

Provides a comprehensive interface for managing document collections,
embeddings, and RAG capabilities with document import/export functionality.
"""

import wx
import wx.lib.scrolledpanel
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import threading
from datetime import datetime

from llamalot.backend import (
    EmbeddingsManager, ConfigurationManager, Document, SearchResult,
    OllamaClient
)
from llamalot.utils.logging_config import get_logger
from llamalot.gui.dialogs import (
    DocumentEditorDialog,
    DocumentImportDialog,
    CollectionManagerDialog
)

logger = get_logger(__name__)


class EmbeddingsPanel(wx.lib.scrolledpanel.ScrolledPanel):
    """
    Main panel for embeddings management with collections, documents, and search.
    
    Features:
    - Collection browser and management
    - Document listing and editing
    - Import/export capabilities
    - Similarity search interface
    - Integration with chat system
    """
    
    def __init__(self, parent):
        """
        Initialize the embeddings management panel.
        
        Args:
            parent: Parent window/panel
        """
        super().__init__(parent)
        self.SetupScrolling()
        
        # Initialize backend
        self.config_manager = ConfigurationManager()
        self.embeddings_manager = EmbeddingsManager(self.config_manager)
        
        # UI state
        self.current_collection = None
        self.selected_documents = []
        self.search_results = []
        
        # Create UI
        self._create_widgets()
        self._create_layout()
        self._bind_events()
        
        # Load initial data
        self._refresh_collections()
        
        logger.info("Embeddings panel initialized")
    
    def _create_widgets(self):
        """Create all UI widgets."""
        
        # === Collections Section ===
        collections_box = wx.StaticBox(self, label="Collections")
        self.collections_sizer = wx.StaticBoxSizer(collections_box, wx.VERTICAL)
        
        # Collections list
        self.collections_list = wx.ListCtrl(
            self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL
        )
        self.collections_list.AppendColumn("Collection", width=200)
        self.collections_list.AppendColumn("Documents", width=80)
        self.collections_list.AppendColumn("Description", width=300)
        
        # Collection buttons
        self.collections_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_new_collection = wx.Button(self, label="New Collection")
        self.btn_edit_collection = wx.Button(self, label="Edit Collection")
        self.btn_delete_collection = wx.Button(self, label="Delete Collection")
        self.btn_refresh_collections = wx.Button(self, label="Refresh")
        
        self.collections_btn_sizer.Add(self.btn_new_collection, 0, wx.RIGHT, 5)
        self.collections_btn_sizer.Add(self.btn_edit_collection, 0, wx.RIGHT, 5)
        self.collections_btn_sizer.Add(self.btn_delete_collection, 0, wx.RIGHT, 5)
        self.collections_btn_sizer.AddStretchSpacer()
        self.collections_btn_sizer.Add(self.btn_refresh_collections, 0)
        
        # === Documents Section ===
        documents_box = wx.StaticBox(self, label="Documents")
        self.documents_sizer = wx.StaticBoxSizer(documents_box, wx.VERTICAL)
        
        # Documents list
        self.documents_list = wx.ListCtrl(
            self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL
        )
        self.documents_list.AppendColumn("ID", width=150)
        self.documents_list.AppendColumn("Content Preview", width=400)
        self.documents_list.AppendColumn("Topic", width=100)
        self.documents_list.AppendColumn("Category", width=100)
        
        # Document buttons
        self.documents_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_add_document = wx.Button(self, label="Add Document")
        self.btn_edit_document = wx.Button(self, label="Edit Document")
        self.btn_delete_document = wx.Button(self, label="Delete Document")
        self.btn_import_documents = wx.Button(self, label="Import Documents")
        
        self.documents_btn_sizer.Add(self.btn_add_document, 0, wx.RIGHT, 5)
        self.documents_btn_sizer.Add(self.btn_edit_document, 0, wx.RIGHT, 5)
        self.documents_btn_sizer.Add(self.btn_delete_document, 0, wx.RIGHT, 5)
        self.documents_btn_sizer.AddStretchSpacer()
        self.documents_btn_sizer.Add(self.btn_import_documents, 0)
        
        # === Search Section ===
        search_box = wx.StaticBox(self, label="Document Search")
        self.search_sizer = wx.StaticBoxSizer(search_box, wx.VERTICAL)
        
        # Search controls
        self.search_ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.search_ctrl_sizer.Add(wx.StaticText(self, label="Query:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        
        self.search_text = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.search_ctrl_sizer.Add(self.search_text, 1, wx.RIGHT, 5)
        
        self.btn_search = wx.Button(self, label="Search")
        self.search_ctrl_sizer.Add(self.btn_search, 0, wx.RIGHT, 5)
        
        self.search_ctrl_sizer.Add(wx.StaticText(self, label="Results:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.search_limit = wx.SpinCtrl(self, value="5", min=1, max=50)
        self.search_ctrl_sizer.Add(self.search_limit, 0)
        
        # Search results
        self.search_results_list = wx.ListCtrl(
            self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL
        )
        self.search_results_list.AppendColumn("Score", width=80)
        self.search_results_list.AppendColumn("Content Preview", width=400)
        self.search_results_list.AppendColumn("Metadata", width=200)
        
        # === Chat Integration Section ===
        chat_box = wx.StaticBox(self, label="Chat Integration")
        self.chat_sizer = wx.StaticBoxSizer(chat_box, wx.VERTICAL)
        
        # Chat controls
        self.chat_ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.chk_enable_rag = wx.CheckBox(self, label="Enable RAG in Chat")
        self.chat_ctrl_sizer.Add(self.chk_enable_rag, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        self.chat_ctrl_sizer.Add(wx.StaticText(self, label="Active Collections:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        
        self.active_collections = wx.ListBox(self, style=wx.LB_MULTIPLE)
        self.chat_ctrl_sizer.Add(self.active_collections, 1, wx.RIGHT, 5)
        
        self.btn_apply_chat_settings = wx.Button(self, label="Apply to Chat")
        self.chat_ctrl_sizer.Add(self.btn_apply_chat_settings, 0)
        
        # === Status Bar ===
        self.status_text = wx.StaticText(self, label="Ready")
        
        # Initially disable document-related buttons
        self._update_ui_state()
    
    def _create_layout(self):
        """Create the layout for all widgets."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Top section: Collections and Documents side by side
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Collections section
        self.collections_sizer.Add(self.collections_list, 1, wx.EXPAND | wx.ALL, 5)
        self.collections_sizer.Add(self.collections_btn_sizer, 0, wx.EXPAND | wx.ALL, 5)
        top_sizer.Add(self.collections_sizer, 1, wx.EXPAND | wx.RIGHT, 5)
        
        # Documents section
        self.documents_sizer.Add(self.documents_list, 1, wx.EXPAND | wx.ALL, 5)
        self.documents_sizer.Add(self.documents_btn_sizer, 0, wx.EXPAND | wx.ALL, 5)
        top_sizer.Add(self.documents_sizer, 2, wx.EXPAND)
        
        main_sizer.Add(top_sizer, 2, wx.EXPAND | wx.ALL, 5)
        
        # Search section
        self.search_sizer.Add(self.search_ctrl_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.search_sizer.Add(self.search_results_list, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.search_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        
        # Chat integration section
        self.chat_sizer.Add(self.chat_ctrl_sizer, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.chat_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        
        # Status bar
        main_sizer.Add(self.status_text, 0, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(main_sizer)
    
    def _bind_events(self):
        """Bind all event handlers."""
        
        # Collection events
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_collection_selected, self.collections_list)
        self.Bind(wx.EVT_BUTTON, self._on_new_collection, self.btn_new_collection)
        self.Bind(wx.EVT_BUTTON, self._on_edit_collection, self.btn_edit_collection)
        self.Bind(wx.EVT_BUTTON, self._on_delete_collection, self.btn_delete_collection)
        self.Bind(wx.EVT_BUTTON, self._on_refresh_collections, self.btn_refresh_collections)
        
        # Document events
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_document_selected, self.documents_list)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_document_activated, self.documents_list)
        self.Bind(wx.EVT_BUTTON, self._on_add_document, self.btn_add_document)
        self.Bind(wx.EVT_BUTTON, self._on_edit_document, self.btn_edit_document)
        self.Bind(wx.EVT_BUTTON, self._on_delete_document, self.btn_delete_document)
        self.Bind(wx.EVT_BUTTON, self._on_import_documents, self.btn_import_documents)
        
        # Search events
        self.Bind(wx.EVT_BUTTON, self._on_search, self.btn_search)
        self.Bind(wx.EVT_TEXT_ENTER, self._on_search, self.search_text)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_search_result_selected, self.search_results_list)
        
        # Chat events
        self.Bind(wx.EVT_BUTTON, self._on_apply_chat_settings, self.btn_apply_chat_settings)
    
    def _update_ui_state(self):
        """Update UI state based on current selection."""
        has_collection = self.current_collection is not None
        has_document = len(self.selected_documents) > 0
        
        # Collection buttons
        self.btn_edit_collection.Enable(has_collection)
        self.btn_delete_collection.Enable(has_collection)
        
        # Document buttons
        self.btn_add_document.Enable(has_collection)
        self.btn_edit_document.Enable(has_document)
        self.btn_delete_document.Enable(has_document)
        self.btn_import_documents.Enable(has_collection)
        
        # Search
        self.btn_search.Enable(has_collection)
        self.search_text.Enable(has_collection)
        
        # Update status
        if has_collection:
            stats = self.embeddings_manager.get_collection_stats(self.current_collection)
            doc_count = stats.get('document_count', 0)
            self.status_text.SetLabel(f"Collection: {self.current_collection} ({doc_count} documents)")
        else:
            self.status_text.SetLabel("Select a collection to manage documents")
    
    def _refresh_collections(self):
        """Refresh the collections list."""
        try:
            self.collections_list.DeleteAllItems()
            collections = self.embeddings_manager.list_collections()
            
            for i, collection_name in enumerate(collections):
                stats = self.embeddings_manager.get_collection_stats(collection_name)
                
                index = self.collections_list.InsertItem(i, collection_name)
                self.collections_list.SetItem(index, 1, str(stats.get('document_count', 0)))
                self.collections_list.SetItem(index, 2, stats.get('description', ''))
            
            # Update active collections list for chat
            self.active_collections.Clear()
            self.active_collections.AppendItems(collections)
            
            logger.info(f"Refreshed collections list: {len(collections)} collections")
            
        except Exception as e:
            logger.error(f"Error refreshing collections: {e}")
            wx.MessageBox(f"Error refreshing collections: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _refresh_documents(self):
        """Refresh the documents list for current collection."""
        if not self.current_collection:
            self.documents_list.DeleteAllItems()
            return
        
        try:
            self.documents_list.DeleteAllItems()
            
            # Get all documents in collection (this is a simplified approach)
            # In a real implementation, you might want pagination
            collection = self.embeddings_manager.get_collection(self.current_collection)
            
            # Get some sample documents using a broad search
            # This is a workaround since ChromaDB doesn't have a direct "list all" method
            all_docs = collection.get(include=['documents', 'metadatas'])
            
            if all_docs and 'documents' in all_docs:
                documents = all_docs['documents']
                metadatas = all_docs.get('metadatas', [])
                ids = all_docs.get('ids', [])
                
                for i, (doc_id, content, metadata) in enumerate(zip(ids, documents, metadatas)):
                    metadata = metadata or {}
                    
                    index = self.documents_list.InsertItem(i, doc_id)
                    preview = content[:100] + "..." if len(content) > 100 else content
                    self.documents_list.SetItem(index, 1, preview)
                    self.documents_list.SetItem(index, 2, metadata.get('topic', ''))
                    self.documents_list.SetItem(index, 3, metadata.get('category', ''))
            
            logger.info(f"Refreshed documents for collection: {self.current_collection}")
            
        except Exception as e:
            logger.error(f"Error refreshing documents: {e}")
            wx.MessageBox(f"Error refreshing documents: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    # === Event Handlers ===
    
    def _on_collection_selected(self, event):
        """Handle collection selection."""
        selection = event.GetIndex()
        if selection >= 0:
            self.current_collection = self.collections_list.GetItemText(selection, 0)
            self._refresh_documents()
            self._update_ui_state()
    
    def _on_document_selected(self, event):
        """Handle document selection."""
        selection = event.GetIndex()
        if selection >= 0:
            doc_id = self.documents_list.GetItemText(selection, 0)
            self.selected_documents = [doc_id]
        else:
            self.selected_documents = []
        self._update_ui_state()
    
    def _on_document_activated(self, event):
        """Handle document double-click (edit)."""
        self._on_edit_document(event)
    
    def _on_new_collection(self, event):
        """Handle new collection creation."""
        with CollectionManagerDialog(self) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                collection_info = dialog.get_collection_info()
                try:
                    success = self.embeddings_manager.create_collection(
                        collection_info['name'],
                        metadata=collection_info['metadata']
                    )
                    if success:
                        self._refresh_collections()
                        wx.MessageBox("Collection created successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
                    
                except Exception as e:
                    logger.error(f"Error creating collection: {e}")
                    wx.MessageBox(f"Error creating collection: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _on_edit_collection(self, event):
        """Handle collection editing."""
        if not self.current_collection:
            return
        
        # Get current collection metadata
        stats = self.embeddings_manager.get_collection_stats(self.current_collection)
        
        with CollectionManagerDialog(self, collection_name=self.current_collection, 
                                   metadata=stats.get('metadata', {})) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                # Collection editing would require recreating the collection
                # For now, show a message about limitations
                wx.MessageBox(
                    "Collection metadata editing requires advanced ChromaDB operations.\n"
                    "This feature will be implemented in a future version.",
                    "Feature Coming Soon",
                    wx.OK | wx.ICON_INFORMATION
                )
    
    def _on_delete_collection(self, event):
        """Handle collection deletion."""
        if not self.current_collection:
            return
        
        dlg = wx.MessageDialog(
            self,
            f"Are you sure you want to delete collection '{self.current_collection}'?\n"
            "This will permanently remove all documents and embeddings.",
            "Confirm Deletion",
            wx.YES_NO | wx.ICON_QUESTION
        )
        
        if dlg.ShowModal() == wx.ID_YES:
            try:
                success = self.embeddings_manager.delete_collection(self.current_collection)
                if success:
                    self.current_collection = None
                    self._refresh_collections()
                    self._refresh_documents()
                    self._update_ui_state()
                    wx.MessageBox("Collection deleted successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
                
            except Exception as e:
                logger.error(f"Error deleting collection: {e}")
                wx.MessageBox(f"Error deleting collection: {e}", "Error", wx.OK | wx.ICON_ERROR)
        
        dlg.Destroy()
    
    def _on_refresh_collections(self, event):
        """Handle collections refresh."""
        self._refresh_collections()
    
    def _on_add_document(self, event):
        """Handle adding new document."""
        if not self.current_collection:
            return
        
        with DocumentEditorDialog(self) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                document = dialog.get_document()
                try:
                    success = self.embeddings_manager.add_document(self.current_collection, document)
                    if success:
                        self._refresh_documents()
                        wx.MessageBox("Document added successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
                
                except Exception as e:
                    logger.error(f"Error adding document: {e}")
                    wx.MessageBox(f"Error adding document: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _on_edit_document(self, event):
        """Handle editing existing document."""
        if not self.selected_documents or not self.current_collection:
            return
        
        doc_id = self.selected_documents[0]
        
        # Get document from collection
        try:
            collection = self.embeddings_manager.get_collection(self.current_collection)
            result = collection.get(ids=[doc_id], include=['documents', 'metadatas'])
            
            if result and 'documents' in result and result['documents']:
                content = result['documents'][0]
                metadata = result.get('metadatas', [{}])[0] or {}
                
                document = Document(id=doc_id, content=content, metadata=metadata)
                
                with DocumentEditorDialog(self, document=document) as dialog:
                    if dialog.ShowModal() == wx.ID_OK:
                        updated_document = dialog.get_document()
                        
                        # Delete old document and add updated one
                        self.embeddings_manager.delete_document(self.current_collection, doc_id)
                        success = self.embeddings_manager.add_document(self.current_collection, updated_document)
                        
                        if success:
                            self._refresh_documents()
                            wx.MessageBox("Document updated successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
            
        except Exception as e:
            logger.error(f"Error editing document: {e}")
            wx.MessageBox(f"Error editing document: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _on_delete_document(self, event):
        """Handle document deletion."""
        if not self.selected_documents or not self.current_collection:
            return
        
        doc_id = self.selected_documents[0]
        
        dlg = wx.MessageDialog(
            self,
            f"Are you sure you want to delete document '{doc_id}'?",
            "Confirm Deletion",
            wx.YES_NO | wx.ICON_QUESTION
        )
        
        if dlg.ShowModal() == wx.ID_YES:
            try:
                success = self.embeddings_manager.delete_document(self.current_collection, doc_id)
                if success:
                    self._refresh_documents()
                    self.selected_documents = []
                    self._update_ui_state()
                    wx.MessageBox("Document deleted successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
                
            except Exception as e:
                logger.error(f"Error deleting document: {e}")
                wx.MessageBox(f"Error deleting document: {e}", "Error", wx.OK | wx.ICON_ERROR)
        
        dlg.Destroy()
    
    def _on_import_documents(self, event):
        """Handle document import."""
        if not self.current_collection:
            return
        
        with DocumentImportDialog(self, collection_name=self.current_collection,
                                embeddings_manager=self.embeddings_manager) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self._refresh_documents()
    
    def _on_search(self, event):
        """Handle document search."""
        if not self.current_collection:
            return
        
        query = self.search_text.GetValue().strip()
        if not query:
            return
        
        try:
            n_results = self.search_limit.GetValue()
            results = self.embeddings_manager.search_similar(
                self.current_collection,
                query,
                n_results=n_results
            )
            
            # Display results
            self.search_results_list.DeleteAllItems()
            self.search_results = results
            
            for i, result in enumerate(results):
                index = self.search_results_list.InsertItem(i, f"{result.score:.3f}")
                preview = result.document.content[:100] + "..." if len(result.document.content) > 100 else result.document.content
                self.search_results_list.SetItem(index, 1, preview)
                
                metadata_str = ", ".join([f"{k}:{v}" for k, v in (result.document.metadata or {}).items()])
                self.search_results_list.SetItem(index, 2, metadata_str)
            
            logger.info(f"Search completed: {len(results)} results for query '{query}'")
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            wx.MessageBox(f"Error searching documents: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _on_search_result_selected(self, event):
        """Handle search result selection."""
        selection = event.GetIndex()
        if 0 <= selection < len(self.search_results):
            result = self.search_results[selection]
            # Could show document details in a separate panel or dialog
            logger.info(f"Selected search result: {result.document.id}")
    
    def _on_apply_chat_settings(self, event):
        """Handle applying chat settings."""
        selected_collections = self.active_collections.GetSelections()
        collection_names = [self.active_collections.GetString(i) for i in selected_collections]
        rag_enabled = self.chk_enable_rag.GetValue()
        
        # Store settings in configuration
        try:
            config = self.config_manager.config
            config.embeddings.rag_enabled = rag_enabled
            config.embeddings.active_collections = collection_names
            self.config_manager.save()
            
            wx.MessageBox(
                f"Chat settings applied!\nRAG enabled: {rag_enabled}\nActive collections: {len(collection_names)}",
                "Settings Applied",
                wx.OK | wx.ICON_INFORMATION
            )
            
            # Notify parent window about chat settings change
            event = wx.PyCommandEvent(wx.EVT_MENU.typeId, self.GetId())
            event.SetString("embeddings_settings_changed")
            wx.PostEvent(self.GetParent(), event)
            
        except Exception as e:
            logger.error(f"Error applying chat settings: {e}")
            wx.MessageBox(f"Error applying chat settings: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def get_active_collections(self) -> List[str]:
        """
        Get currently active collections for chat integration.
        
        Returns:
            List of active collection names
        """
        if not self.chk_enable_rag.GetValue():
            return []
        
        selected_collections = self.active_collections.GetSelections()
        return [self.active_collections.GetString(i) for i in selected_collections]
    
    def is_rag_enabled(self) -> bool:
        """
        Check if RAG is currently enabled.
        
        Returns:
            True if RAG is enabled for chat
        """
        return self.chk_enable_rag.GetValue()
    
    def search_for_context(self, query: str, max_results: int = 3) -> List[SearchResult]:
        """
        Search for context across active collections for chat integration.
        
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
        
        all_results = []
        
        for collection_name in active_collections:
            try:
                results = self.embeddings_manager.search_similar(
                    collection_name,
                    query,
                    n_results=max_results
                )
                all_results.extend(results)
                
            except Exception as e:
                logger.error(f"Error searching collection {collection_name}: {e}")
        
        # Sort by score and limit results
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:max_results]

"""
Document Editor Dialog for LlamaLot embeddings management.

Provides interface for creating and editing documents with metadata.
"""

import wx
import logging
from typing import Dict, Any, Optional, Tuple
import uuid
from datetime import datetime

from llamalot.backend import Document
from llamalot.utils.logging_config import get_logger

logger = get_logger(__name__)


class DocumentEditorDialog(wx.Dialog):
    """
    Dialog for creating and editing documents with metadata support.
    
    Features:
    - Document ID management
    - Rich text content editing
    - Metadata key-value editing
    - Content preview and validation
    """
    
    def __init__(self, parent, document: Optional[Document] = None):
        """
        Initialize the document editor dialog.
        
        Args:
            parent: Parent window
            document: Existing document to edit (None for new document)
        """
        super().__init__(
            parent, 
            title="Document Editor" if document else "New Document",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=(800, 600)
        )
        
        self.document = document
        self.is_editing = document is not None
        
        self._create_widgets()
        self._create_layout()
        self._bind_events()
        
        if self.document:
            self._load_document()
        else:
            # Generate new document ID
            self.document_id.SetValue(f"doc_{uuid.uuid4().hex[:8]}")
        
        logger.info(f"Document editor dialog initialized (editing: {self.is_editing})")
    
    def _create_widgets(self):
        """Create all UI widgets."""
        
        # === Document Info Section ===
        info_box = wx.StaticBox(self, label="Document Information")
        self.info_sizer = wx.StaticBoxSizer(info_box, wx.VERTICAL)
        
        # Document ID
        id_sizer = wx.BoxSizer(wx.HORIZONTAL)
        id_sizer.Add(wx.StaticText(self, label="Document ID:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.document_id = wx.TextCtrl(self, size=(200, -1))
        id_sizer.Add(self.document_id, 1)
        
        # Auto-generate ID button
        self.btn_generate_id = wx.Button(self, label="Generate ID", size=(100, -1))
        id_sizer.Add(self.btn_generate_id, 0, wx.LEFT, 5)
        
        # === Content Section ===
        content_box = wx.StaticBox(self, label="Document Content")
        self.content_sizer = wx.StaticBoxSizer(content_box, wx.VERTICAL)
        
        # Content text area
        self.content_text = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_WORDWRAP
        )
        
        # Content stats
        self.content_stats = wx.StaticText(self, label="Characters: 0, Words: 0")
        
        # === Metadata Section ===
        metadata_box = wx.StaticBox(self, label="Metadata")
        self.metadata_sizer = wx.StaticBoxSizer(metadata_box, wx.VERTICAL)
        
        # Common metadata fields
        metadata_grid = wx.FlexGridSizer(3, 2, 5, 10)
        metadata_grid.AddGrowableCol(1)
        
        # Topic
        metadata_grid.Add(wx.StaticText(self, label="Topic:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.metadata_topic = wx.TextCtrl(self)
        metadata_grid.Add(self.metadata_topic, 1, wx.EXPAND)
        
        # Category
        metadata_grid.Add(wx.StaticText(self, label="Category:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.metadata_category = wx.TextCtrl(self)
        metadata_grid.Add(self.metadata_category, 1, wx.EXPAND)
        
        # Source
        metadata_grid.Add(wx.StaticText(self, label="Source:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.metadata_source = wx.TextCtrl(self)
        metadata_grid.Add(self.metadata_source, 1, wx.EXPAND)
        
        # Custom metadata list
        custom_metadata_label = wx.StaticText(self, label="Custom Metadata:")
        
        self.metadata_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_EDIT_LABELS)
        self.metadata_list.AppendColumn("Key", width=150)
        self.metadata_list.AppendColumn("Value", width=250)
        
        # Metadata management buttons
        metadata_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_add_metadata = wx.Button(self, label="Add Metadata")
        self.btn_edit_metadata = wx.Button(self, label="Edit Selected")
        self.btn_remove_metadata = wx.Button(self, label="Remove Selected")
        
        metadata_btn_sizer.Add(self.btn_add_metadata, 0, wx.RIGHT, 5)
        metadata_btn_sizer.Add(self.btn_edit_metadata, 0, wx.RIGHT, 5)
        metadata_btn_sizer.Add(self.btn_remove_metadata, 0)
        
        # === Preview Section ===
        preview_box = wx.StaticBox(self, label="Document Preview")
        self.preview_sizer = wx.StaticBoxSizer(preview_box, wx.VERTICAL)
        
        self.preview_text = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP
        )
        
        self.btn_refresh_preview = wx.Button(self, label="Refresh Preview")
        
        # === Dialog Buttons ===
        self.btn_save = wx.Button(self, wx.ID_OK, "Save Document")
        self.btn_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        
        # Validation
        self._update_save_button()
    
    def _create_layout(self):
        """Create the layout for all widgets."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Document info section with proper sizer reference
        id_sizer = wx.BoxSizer(wx.HORIZONTAL)
        id_sizer.Add(wx.StaticText(self, label="Document ID:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        id_sizer.Add(self.document_id, 1)
        id_sizer.Add(self.btn_generate_id, 0, wx.LEFT, 5)
        
        self.info_sizer.Add(id_sizer, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.info_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Content section
        self.content_sizer.Add(self.content_text, 1, wx.EXPAND | wx.ALL, 5)
        self.content_sizer.Add(self.content_stats, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        main_sizer.Add(self.content_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        
        # Metadata section with proper sizer references
        metadata_grid = wx.FlexGridSizer(3, 2, 5, 10)
        metadata_grid.AddGrowableCol(1)
        
        # Topic
        metadata_grid.Add(wx.StaticText(self, label="Topic:"), 0, wx.ALIGN_CENTER_VERTICAL)
        metadata_grid.Add(self.metadata_topic, 1, wx.EXPAND)
        
        # Category
        metadata_grid.Add(wx.StaticText(self, label="Category:"), 0, wx.ALIGN_CENTER_VERTICAL)
        metadata_grid.Add(self.metadata_category, 1, wx.EXPAND)
        
        # Source
        metadata_grid.Add(wx.StaticText(self, label="Source:"), 0, wx.ALIGN_CENTER_VERTICAL)
        metadata_grid.Add(self.metadata_source, 1, wx.EXPAND)
        
        # Custom metadata label
        custom_metadata_label = wx.StaticText(self, label="Custom Metadata:")
        
        # Metadata management buttons
        metadata_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        metadata_btn_sizer.Add(self.btn_add_metadata, 0, wx.RIGHT, 5)
        metadata_btn_sizer.Add(self.btn_edit_metadata, 0, wx.RIGHT, 5)
        metadata_btn_sizer.Add(self.btn_remove_metadata, 0)
        
        self.metadata_sizer.Add(metadata_grid, 0, wx.EXPAND | wx.ALL, 5)
        self.metadata_sizer.Add(custom_metadata_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        self.metadata_sizer.Add(self.metadata_list, 1, wx.EXPAND | wx.ALL, 5)
        self.metadata_sizer.Add(metadata_btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        main_sizer.Add(self.metadata_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        
        # Preview section
        self.preview_sizer.Add(self.preview_text, 1, wx.EXPAND | wx.ALL, 5)
        self.preview_sizer.Add(self.btn_refresh_preview, 0, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        main_sizer.Add(self.preview_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        
        # Dialog buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(self.btn_save, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_cancel, 0)
        
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(main_sizer)
    
    def _bind_events(self):
        """Bind all event handlers."""
        
        # Document ID events
        self.Bind(wx.EVT_BUTTON, self._on_generate_id, self.btn_generate_id)
        self.Bind(wx.EVT_TEXT, self._on_text_changed, self.document_id)
        
        # Content events
        self.Bind(wx.EVT_TEXT, self._on_content_changed, self.content_text)
        
        # Metadata events
        self.Bind(wx.EVT_TEXT, self._on_text_changed, self.metadata_topic)
        self.Bind(wx.EVT_TEXT, self._on_text_changed, self.metadata_category)
        self.Bind(wx.EVT_TEXT, self._on_text_changed, self.metadata_source)
        
        self.Bind(wx.EVT_BUTTON, self._on_add_metadata, self.btn_add_metadata)
        self.Bind(wx.EVT_BUTTON, self._on_edit_metadata, self.btn_edit_metadata)
        self.Bind(wx.EVT_BUTTON, self._on_remove_metadata, self.btn_remove_metadata)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_metadata_selected, self.metadata_list)
        
        # Preview events
        self.Bind(wx.EVT_BUTTON, self._on_refresh_preview, self.btn_refresh_preview)
    
    def _load_document(self):
        """Load existing document data into the form."""
        if not self.document:
            return
        
        # Load basic info
        self.document_id.SetValue(self.document.id)
        self.content_text.SetValue(self.document.content)
        
        # Load metadata
        metadata = self.document.metadata or {}
        
        # Load common metadata fields
        self.metadata_topic.SetValue(metadata.get('topic', ''))
        self.metadata_category.SetValue(metadata.get('category', ''))
        self.metadata_source.SetValue(metadata.get('source', ''))
        
        # Load custom metadata
        common_keys = {'topic', 'category', 'source'}
        for key, value in metadata.items():
            if key not in common_keys:
                self._add_metadata_item(key, str(value))
        
        # Update UI
        self._update_content_stats()
        self._refresh_preview()
        
        logger.info(f"Loaded document: {self.document.id}")
    
    def _add_metadata_item(self, key: str, value: str):
        """Add a metadata item to the list."""
        index = self.metadata_list.GetItemCount()
        self.metadata_list.InsertItem(index, key)
        self.metadata_list.SetItem(index, 1, value)
    
    def _update_content_stats(self):
        """Update content statistics display."""
        content = self.content_text.GetValue()
        char_count = len(content)
        word_count = len(content.split()) if content.strip() else 0
        
        self.content_stats.SetLabel(f"Characters: {char_count}, Words: {word_count}")
    
    def _update_save_button(self):
        """Update save button state based on validation."""
        doc_id = self.document_id.GetValue().strip()
        content = self.content_text.GetValue().strip()
        
        # Basic validation
        is_valid = bool(doc_id and content)
        self.btn_save.Enable(is_valid)
    
    def _refresh_preview(self):
        """Refresh the document preview."""
        try:
            document = self.get_document()
            
            preview_lines = [
                f"ID: {document.id}",
                f"Content Length: {len(document.content)} characters",
                "",
                "Content Preview:",
                "-" * 40,
                document.content[:500] + ("..." if len(document.content) > 500 else ""),
                "",
                "Metadata:",
                "-" * 40
            ]
            
            for key, value in (document.metadata or {}).items():
                preview_lines.append(f"{key}: {value}")
            
            self.preview_text.SetValue("\n".join(preview_lines))
            
        except Exception as e:
            self.preview_text.SetValue(f"Preview error: {e}")
    
    # === Event Handlers ===
    
    def _on_generate_id(self, event):
        """Generate a new document ID."""
        new_id = f"doc_{uuid.uuid4().hex[:8]}"
        self.document_id.SetValue(new_id)
    
    def _on_text_changed(self, event):
        """Handle text field changes."""
        self._update_save_button()
        event.Skip()
    
    def _on_content_changed(self, event):
        """Handle content text changes."""
        self._update_content_stats()
        self._update_save_button()
        event.Skip()
    
    def _on_add_metadata(self, event):
        """Add custom metadata entry."""
        with MetadataEntryDialog(self) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                key, value = dialog.get_metadata()
                if key and value:
                    self._add_metadata_item(key, value)
    
    def _on_edit_metadata(self, event):
        """Edit selected metadata entry."""
        selection = self.metadata_list.GetFirstSelected()
        if selection == -1:
            return
        
        current_key = self.metadata_list.GetItemText(selection, 0)
        current_value = self.metadata_list.GetItemText(selection, 1)
        
        with MetadataEntryDialog(self, key=current_key, value=current_value) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                key, value = dialog.get_metadata()
                if key and value:
                    self.metadata_list.SetItem(selection, 0, key)
                    self.metadata_list.SetItem(selection, 1, value)
    
    def _on_remove_metadata(self, event):
        """Remove selected metadata entry."""
        selection = self.metadata_list.GetFirstSelected()
        if selection != -1:
            self.metadata_list.DeleteItem(selection)
    
    def _on_metadata_selected(self, event):
        """Handle metadata list selection."""
        has_selection = self.metadata_list.GetFirstSelected() != -1
        self.btn_edit_metadata.Enable(has_selection)
        self.btn_remove_metadata.Enable(has_selection)
    
    def _on_refresh_preview(self, event):
        """Handle preview refresh."""
        self._refresh_preview()
    
    def get_document(self) -> Document:
        """
        Get the document from the form data.
        
        Returns:
            Document object with current form data
        """
        # Collect metadata
        metadata = {}
        
        # Common metadata fields
        topic = self.metadata_topic.GetValue().strip()
        if topic:
            metadata['topic'] = topic
        
        category = self.metadata_category.GetValue().strip()
        if category:
            metadata['category'] = category
        
        source = self.metadata_source.GetValue().strip()
        if source:
            metadata['source'] = source
        
        # Custom metadata from list
        for i in range(self.metadata_list.GetItemCount()):
            key = self.metadata_list.GetItemText(i, 0)
            value = self.metadata_list.GetItemText(i, 1)
            if key and value:
                metadata[key] = value
        
        # Add system metadata
        if not self.is_editing:
            metadata['created_at'] = datetime.now().isoformat()
        metadata['modified_at'] = datetime.now().isoformat()
        
        return Document(
            id=self.document_id.GetValue().strip(),
            content=self.content_text.GetValue().strip(),
            metadata=metadata if metadata else None
        )


class MetadataEntryDialog(wx.Dialog):
    """Simple dialog for entering metadata key-value pairs."""
    
    def __init__(self, parent, key: str = "", value: str = ""):
        """
        Initialize metadata entry dialog.
        
        Args:
            parent: Parent window
            key: Initial key value
            value: Initial value
        """
        super().__init__(
            parent,
            title="Metadata Entry",
            style=wx.DEFAULT_DIALOG_STYLE
        )
        
        self._create_widgets(key, value)
        self._create_layout()
    
    def _create_widgets(self, key: str, value: str):
        """Create dialog widgets."""
        
        # Key field
        key_label = wx.StaticText(self, label="Key:")
        self.key_text = wx.TextCtrl(self, value=key)
        
        # Value field
        value_label = wx.StaticText(self, label="Value:")
        self.value_text = wx.TextCtrl(self, value=value)
        
        # Buttons
        self.btn_ok = wx.Button(self, wx.ID_OK, "OK")
        self.btn_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        
        # Store references for layout
        self.key_label = key_label
        self.value_label = value_label
    
    def _create_layout(self):
        """Create dialog layout."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Form fields
        form_sizer = wx.FlexGridSizer(2, 2, 5, 10)
        form_sizer.AddGrowableCol(1)
        
        form_sizer.Add(self.key_label, 0, wx.ALIGN_CENTER_VERTICAL)
        form_sizer.Add(self.key_text, 1, wx.EXPAND)
        form_sizer.Add(self.value_label, 0, wx.ALIGN_CENTER_VERTICAL)
        form_sizer.Add(self.value_text, 1, wx.EXPAND)
        
        main_sizer.Add(form_sizer, 1, wx.EXPAND | wx.ALL, 10)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(self.btn_ok, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_cancel, 0)
        
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(main_sizer)
    
    def get_metadata(self) -> Tuple[str, str]:
        """
        Get the metadata key-value pair.
        
        Returns:
            Tuple of (key, value)
        """
        return self.key_text.GetValue().strip(), self.value_text.GetValue().strip()

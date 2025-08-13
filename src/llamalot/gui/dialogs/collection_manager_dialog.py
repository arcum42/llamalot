"""
Collection Manager Dialog for LlamaLot embeddings management.

Provides interface for creating and managing document collections.
"""

import wx
import logging
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from llamalot.utils.logging_config import get_logger

logger = get_logger(__name__)


class CollectionManagerDialog(wx.Dialog):
    """
    Dialog for creating and managing document collections.
    
    Features:
    - Collection creation and editing
    - Metadata management
    - Collection validation
    """
    
    def __init__(self, parent, collection_name: Optional[str] = None, collection_metadata: Optional[Dict] = None):
        """
        Initialize the collection manager dialog.
        
        Args:
            parent: Parent window
            collection_name: Existing collection name (None for new collection)
            collection_metadata: Existing collection metadata
        """
        super().__init__(
            parent,
            title="Collection Manager" if collection_name else "New Collection",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=wx.Size(600, 800)  # Made dialog taller to fit all content properly
        )
        
        self.collection_name = collection_name
        self.collection_metadata = collection_metadata or {}
        self.is_editing = collection_name is not None
        
        self._create_widgets()
        self._create_layout()
        self._bind_events()
        
        if self.is_editing:
            self._load_collection_data()
        
        logger.info(f"Collection manager dialog initialized (editing: {self.is_editing})")
    
    def _create_widgets(self):
        """Create all UI widgets."""
        
        # === Collection Info Section ===
        info_box = wx.StaticBox(self, label="Collection Information")
        self.info_sizer = wx.StaticBoxSizer(info_box, wx.VERTICAL)
        
        # Collection name controls (layout will be created later)
        self.collection_name_ctrl = wx.TextCtrl(self)
        self.btn_generate_name = wx.Button(self, label="Generate Name")
        
        # Description
        self.description_ctrl = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE,
            value=""
        )
        
        # === Metadata Section ===
        metadata_box = wx.StaticBox(self, label="Collection Metadata")
        self.metadata_sizer = wx.StaticBoxSizer(metadata_box, wx.VERTICAL)
        
        # Common metadata fields
        self.metadata_category = wx.TextCtrl(self)
        self.metadata_topic = wx.TextCtrl(self)
        self.metadata_language = wx.ComboBox(
            self,
            choices=["English", "Spanish", "French", "German", "Italian", "Portuguese", "Other"],
            style=wx.CB_DROPDOWN
        )
        self.metadata_language.SetSelection(0)  # Default to English
        self.metadata_owner = wx.TextCtrl(self)
        
        # Custom metadata list
        self.metadata_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_EDIT_LABELS)
        self.metadata_list.AppendColumn("Key", width=150)
        self.metadata_list.AppendColumn("Value", width=250)
        
        # Metadata management buttons
        self.btn_add_metadata = wx.Button(self, label="Add Metadata")
        self.btn_edit_metadata = wx.Button(self, label="Edit Selected")
        self.btn_remove_metadata = wx.Button(self, label="Remove Selected")
        
        # === Collection Settings ===
        settings_box = wx.StaticBox(self, label="Collection Settings")
        self.settings_sizer = wx.StaticBoxSizer(settings_box, wx.VERTICAL)
        
        # Persistence settings
        self.persist_collection = wx.CheckBox(self, label="Make collection persistent")
        self.persist_collection.SetValue(True)  # Default to persistent
        
        # === Preview Section ===
        preview_box = wx.StaticBox(self, label="Collection Preview")
        self.preview_sizer = wx.StaticBoxSizer(preview_box, wx.VERTICAL)
        
        self.preview_text = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP
        )
        
        self.btn_refresh_preview = wx.Button(self, label="Refresh Preview")
        
        # === Dialog Buttons ===
        self.btn_save = wx.Button(self, wx.ID_OK, "Create Collection" if not self.is_editing else "Save Changes")
        self.btn_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        
        # Validation
        self._update_save_button()
    
    def _create_layout(self):
        """Create the layout for all widgets."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Collection info section - create layout elements here
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_sizer.Add(wx.StaticText(self, label="Collection Name:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        name_sizer.Add(self.collection_name_ctrl, 1)
        name_sizer.Add(self.btn_generate_name, 0, wx.LEFT, 5)
        
        desc_label = wx.StaticText(self, label="Description:")
        
        self.info_sizer.Add(name_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.info_sizer.Add(desc_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        self.info_sizer.Add(self.description_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.info_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Metadata section - create layout elements here
        metadata_grid = wx.FlexGridSizer(4, 2, 5, 10)
        metadata_grid.AddGrowableCol(1)
        
        # Category
        metadata_grid.Add(wx.StaticText(self, label="Category:"), 0, wx.ALIGN_CENTER_VERTICAL)
        metadata_grid.Add(self.metadata_category, 1, wx.EXPAND)
        
        # Topic
        metadata_grid.Add(wx.StaticText(self, label="Topic:"), 0, wx.ALIGN_CENTER_VERTICAL)
        metadata_grid.Add(self.metadata_topic, 1, wx.EXPAND)
        
        # Language
        metadata_grid.Add(wx.StaticText(self, label="Language:"), 0, wx.ALIGN_CENTER_VERTICAL)
        metadata_grid.Add(self.metadata_language, 1, wx.EXPAND)
        
        # Owner
        metadata_grid.Add(wx.StaticText(self, label="Owner:"), 0, wx.ALIGN_CENTER_VERTICAL)
        metadata_grid.Add(self.metadata_owner, 1, wx.EXPAND)
        
        custom_metadata_label = wx.StaticText(self, label="Custom Metadata:")
        
        metadata_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        metadata_btn_sizer.Add(self.btn_add_metadata, 0, wx.RIGHT, 5)
        metadata_btn_sizer.Add(self.btn_edit_metadata, 0, wx.RIGHT, 5)
        metadata_btn_sizer.Add(self.btn_remove_metadata, 0)
        
        self.metadata_sizer.Add(metadata_grid, 0, wx.EXPAND | wx.ALL, 5)
        self.metadata_sizer.Add(custom_metadata_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        self.metadata_sizer.Add(self.metadata_list, 1, wx.EXPAND | wx.ALL, 5)
        self.metadata_sizer.Add(metadata_btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        main_sizer.Add(self.metadata_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        
        # Settings section - create layout elements here
        vector_info = wx.StaticText(
            self,
            label="Note: Vector dimension and distance metric are determined by the embedding model."
        )
        vector_info.SetFont(vector_info.GetFont().MakeItalic())
        
        self.settings_sizer.Add(vector_info, 0, wx.EXPAND | wx.ALL, 5)
        self.settings_sizer.Add(self.persist_collection, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.settings_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        
        # Preview section
        self.preview_sizer.Add(self.preview_text, 1, wx.EXPAND | wx.ALL, 5)
        self.preview_sizer.Add(self.btn_refresh_preview, 0, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        main_sizer.Add(self.preview_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        
        # Dialog buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(self.btn_save, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_cancel, 0)
        
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(main_sizer)
    
    def _bind_events(self):
        """Bind all event handlers."""
        
        # Collection name events
        self.Bind(wx.EVT_BUTTON, self._on_generate_name, self.btn_generate_name)
        self.Bind(wx.EVT_TEXT, self._on_text_changed, self.collection_name_ctrl)
        
        # Description events
        self.Bind(wx.EVT_TEXT, self._on_text_changed, self.description_ctrl)
        
        # Metadata events
        self.Bind(wx.EVT_TEXT, self._on_text_changed, self.metadata_category)
        self.Bind(wx.EVT_TEXT, self._on_text_changed, self.metadata_topic)
        self.Bind(wx.EVT_COMBOBOX, self._on_text_changed, self.metadata_language)
        self.Bind(wx.EVT_TEXT, self._on_text_changed, self.metadata_owner)
        
        self.Bind(wx.EVT_BUTTON, self._on_add_metadata, self.btn_add_metadata)
        self.Bind(wx.EVT_BUTTON, self._on_edit_metadata, self.btn_edit_metadata)
        self.Bind(wx.EVT_BUTTON, self._on_remove_metadata, self.btn_remove_metadata)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_metadata_selected, self.metadata_list)
        
        # Preview events
        self.Bind(wx.EVT_BUTTON, self._on_refresh_preview, self.btn_refresh_preview)
        
        # Initially update metadata button states
        self._on_metadata_selected(None)
    
    def _load_collection_data(self):
        """Load existing collection data into the form."""
        if not self.collection_name:
            return
        
        # Load basic info
        self.collection_name_ctrl.SetValue(self.collection_name)
        
        # Load metadata
        metadata = self.collection_metadata
        
        # Load common metadata fields
        self.description_ctrl.SetValue(metadata.get('description', ''))
        self.metadata_category.SetValue(metadata.get('category', ''))
        self.metadata_topic.SetValue(metadata.get('topic', ''))
        self.metadata_owner.SetValue(metadata.get('owner', ''))
        
        # Set language if present
        language = metadata.get('language', 'English')
        choices = [self.metadata_language.GetString(i) for i in range(self.metadata_language.GetCount())]
        if language in choices:
            self.metadata_language.SetSelection(choices.index(language))
        else:
            self.metadata_language.SetValue(language)
        
        # Load custom metadata
        common_keys = {'description', 'category', 'topic', 'language', 'owner', 'created_at', 'modified_at'}
        for key, value in metadata.items():
            if key not in common_keys:
                self._add_metadata_item(key, str(value))
        
        # Update UI
        self._refresh_preview()
        
        logger.info(f"Loaded collection: {self.collection_name}")
    
    def _add_metadata_item(self, key: str, value: str):
        """Add a metadata item to the list."""
        index = self.metadata_list.GetItemCount()
        self.metadata_list.InsertItem(index, key)
        self.metadata_list.SetItem(index, 1, value)
    
    def _update_save_button(self):
        """Update save button state based on validation."""
        collection_name = self.collection_name_ctrl.GetValue().strip()
        
        # Basic validation - collection name is required
        is_valid = bool(collection_name)
        
        # Additional validation - check for valid collection name
        if is_valid:
            # ChromaDB collection names must be 3-63 characters, alphanumeric + _ - .
            import re
            if not re.match(r'^[a-zA-Z0-9_.-]{3,63}$', collection_name):
                is_valid = False
        
        self.btn_save.Enable(is_valid)
    
    def _refresh_preview(self):
        """Refresh the collection preview."""
        try:
            collection_data = self.get_collection_data()
            
            preview_lines = [
                f"Collection Name: {collection_data['name']}",
                f"Description: {collection_data.get('description', 'No description')}",
                f"Persistent: {'Yes' if self.persist_collection.GetValue() else 'No'}",
                "",
                "Metadata:",
                "-" * 40
            ]
            
            metadata = collection_data.get('metadata', {})
            for key, value in metadata.items():
                preview_lines.append(f"{key}: {value}")
            
            if not metadata:
                preview_lines.append("No metadata defined")
            
            self.preview_text.SetValue("\n".join(preview_lines))
            
        except Exception as e:
            self.preview_text.SetValue(f"Preview error: {e}")
    
    # === Event Handlers ===
    
    def _on_generate_name(self, event):
        """Generate a new collection name."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        category = self.metadata_category.GetValue().strip()
        
        if category:
            # Use category in name
            new_name = f"{category.lower().replace(' ', '_')}_{timestamp}"
        else:
            # Generic name
            new_name = f"collection_{timestamp}"
        
        self.collection_name_ctrl.SetValue(new_name)
    
    def _on_text_changed(self, event):
        """Handle text field changes."""
        self._update_save_button()
        if event:
            event.Skip()
    
    def _on_add_metadata(self, event):
        """Add custom metadata entry."""
        from .document_editor_dialog import MetadataEntryDialog
        
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
        
        from .document_editor_dialog import MetadataEntryDialog
        
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
    
    def get_collection_data(self) -> Dict[str, Any]:
        """
        Get the collection data from the form.
        
        Returns:
            Dictionary with collection name and metadata
        """
        # Collect metadata
        metadata = {}
        
        # Description (special handling as it's not in the metadata section)
        description = self.description_ctrl.GetValue().strip()
        if description:
            metadata['description'] = description
        
        # Common metadata fields
        category = self.metadata_category.GetValue().strip()
        if category:
            metadata['category'] = category
        
        topic = self.metadata_topic.GetValue().strip()
        if topic:
            metadata['topic'] = topic
        
        language = self.metadata_language.GetValue().strip()
        if language:
            metadata['language'] = language
        
        owner = self.metadata_owner.GetValue().strip()
        if owner:
            metadata['owner'] = owner
        
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
        
        return {
            'name': self.collection_name_ctrl.GetValue().strip(),
            'metadata': metadata,
            'persist': self.persist_collection.GetValue()
        }

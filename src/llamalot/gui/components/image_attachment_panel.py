"""
Reusable image attachment panel component.

Provides a complete image attachment interface that can be used
in any wxPython application or panel.
"""

import wx
import os
import logging
from typing import List, Optional, Callable
from pathlib import Path

from llamalot.models.chat import ChatImage
from llamalot.utils.logging_config import get_logger
from llamalot.gui.components.selectable_image_panel import SelectableImagePanel
from llamalot.gui.dialogs.image_viewer_dialog import ImageViewerDialog

logger = get_logger(__name__)


class ImageAttachmentPanel(wx.Panel):
    """
    Reusable image attachment panel with preview functionality.
    
    Features:
    - Collapsible image attachment interface
    - Multiple image selection and preview with selection support
    - Image removal functionality (individual and bulk)
    - Double-click to view full-size with clipboard copy
    - Directory memory during session
    - Callback notifications for image changes
    """
    
    def __init__(self, parent: wx.Window, label: str = "📎 Image Attachments", 
                 on_images_changed: Optional[Callable[[List[ChatImage]], None]] = None):
        """
        Initialize the image attachment panel.
        
        Args:
            parent: Parent window/panel
            label: Label for the collapsible pane
            on_images_changed: Optional callback called when images are added/removed
        """
        super().__init__(parent)
        
        self.on_images_changed = on_images_changed
        self.attached_images: List[ChatImage] = []
        self.selected_images: List[ChatImage] = []  # Track selected images
        self.image_panels: List[SelectableImagePanel] = []  # Track image panels by list instead of dict
        self.last_image_directory = ""  # Remember last directory for file dialog
        
        self._create_ui(label)
        self._bind_events()
        
    def _create_ui(self, label: str) -> None:
        """Create the user interface."""
        # Main sizer for the panel
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create collapsible pane
        self.image_collapsible = wx.CollapsiblePane(self, label=label)
        self.image_panel = self.image_collapsible.GetPane()
        
        # Controls sizer (inside collapsible pane)
        controls_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Attachment controls
        self._create_attachment_controls(controls_sizer)
        
        # Image preview area
        self._create_preview_area(controls_sizer)
        
        self.image_panel.SetSizer(controls_sizer)
        
        # Hide collapsible pane initially
        self.image_collapsible.Hide()
        
        main_sizer.Add(self.image_collapsible, 1, wx.EXPAND)
        self.SetSizer(main_sizer)
        
    def _create_attachment_controls(self, parent_sizer: wx.BoxSizer) -> None:
        """Create the attachment control buttons."""
        attach_controls_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.attach_btn = wx.Button(self.image_panel, label="📎 Attach Images", size=wx.Size(120, 25))
        self.delete_selected_btn = wx.Button(self.image_panel, label="🗑️ Delete Selected", size=wx.Size(100, 25))
        self.clear_images_btn = wx.Button(self.image_panel, label="🗑️ Clear All", size=wx.Size(80, 25))
        
        # Initially disable delete selected button
        self.delete_selected_btn.Enable(False)
        
        attach_controls_sizer.Add(self.attach_btn, 0)
        attach_controls_sizer.AddSpacer(5)
        attach_controls_sizer.Add(self.delete_selected_btn, 0)
        attach_controls_sizer.AddSpacer(5)
        attach_controls_sizer.Add(self.clear_images_btn, 0)
        
        parent_sizer.Add(attach_controls_sizer, 0, wx.ALL, 5)
        
    def _create_preview_area(self, parent_sizer: wx.BoxSizer) -> None:
        """Create the image preview area."""
        # Image preview area with container for better sizer management
        self.image_scroll = wx.ScrolledWindow(self.image_panel, style=wx.HSCROLL)
        self.image_scroll.SetScrollRate(20, 0)  # Only horizontal scrolling
        self.image_scroll.SetMinSize(wx.Size(-1, 120))
        
        # Container panel inside scroll window
        self.image_container = wx.Panel(self.image_scroll)
        self.image_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.image_container.SetSizer(self.image_sizer)
        
        # Sizer for the scroll window
        scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        scroll_sizer.Add(self.image_container, 1, wx.EXPAND)
        self.image_scroll.SetSizer(scroll_sizer)
        
        parent_sizer.Add(self.image_scroll, 1, wx.EXPAND | wx.ALL, 5)
        
    def _bind_events(self) -> None:
        """Bind event handlers."""
        self.Bind(wx.EVT_BUTTON, self.on_attach_images, self.attach_btn)
        self.Bind(wx.EVT_BUTTON, self.on_delete_selected, self.delete_selected_btn)
        self.Bind(wx.EVT_BUTTON, self.on_clear_images, self.clear_images_btn)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_image_pane_changed, self.image_collapsible)
        
    # Public API methods
    def show_panel(self, show: bool = True) -> None:
        """Show or hide the image attachment panel."""
        if show:
            self.image_collapsible.Show()
            if not self.image_collapsible.IsExpanded():
                self.image_collapsible.Expand()
        else:
            self.image_collapsible.Hide()
        self.GetParent().Layout()
        
    def get_attached_images(self) -> List[ChatImage]:
        """Get the list of attached images."""
        return self.attached_images.copy()
        
    def clear_images(self) -> None:
        """Clear all attached images."""
        self._clear_attached_images()
        
    def add_images_from_paths(self, file_paths: List[str]) -> None:
        """Add images from file paths."""
        for file_path in file_paths:
            try:
                chat_image = ChatImage.from_file_path(file_path)
                if chat_image:
                    self.attached_images.append(chat_image)
                    self._add_image_preview(chat_image)
                    logger.info(f"Attached image: {chat_image.filename} ({(chat_image.size or 0) / 1024:.1f} KB)")
            except Exception as e:
                logger.error(f"Error loading image from {file_path}: {e}")
                wx.MessageBox(f"Error loading image {file_path}: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
        
        # Notify callback
        if self.on_images_changed:
            self.on_images_changed(self.attached_images)
    
    # Event handlers
    def on_image_pane_changed(self, event: wx.CollapsiblePaneEvent) -> None:
        """Handle collapsible pane state change."""
        self.GetParent().Layout()

    def on_attach_images(self, event: wx.CommandEvent) -> None:
        """Handle image attachment button click."""
        # Create file dialog for image selection
        wildcard = "Image files (*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp)|*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp"
        
        # Use last directory or current working directory as default
        default_dir = self.last_image_directory or os.getcwd()
        
        with wx.FileDialog(
            self, 
            "Select images to attach",
            defaultDir=default_dir,
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST
        ) as dialog:
            
            if dialog.ShowModal() == wx.ID_OK:
                paths = dialog.GetPaths()
                
                # Update last directory for next time
                if paths:
                    self.last_image_directory = os.path.dirname(paths[0])
                    logger.debug(f"Updated last image directory to: {self.last_image_directory}")
                
                self.add_images_from_paths(paths)

    def on_clear_images(self, event: wx.CommandEvent) -> None:
        """Handle clear images button click."""
        self._clear_attached_images()

    def on_delete_selected(self, event: wx.CommandEvent) -> None:
        """Handle delete selected images button click."""
        if not self.selected_images:
            return
            
        # Create a copy of the list to avoid modification during iteration
        images_to_remove = list(self.selected_images)
        
        # Find and remove each selected image panel
        for chat_image in images_to_remove:
            # Find the corresponding panel
            img_panel = None
            for panel in self.image_panels:
                if panel.chat_image == chat_image:
                    img_panel = panel
                    break
            
            if img_panel:
                self._remove_image_preview(img_panel, chat_image)
        
        # Clear selection (should be empty now anyway)
        self.selected_images.clear()
        self._update_delete_button_state()

    def _update_delete_button_state(self) -> None:
        """Update the delete selected button state based on selection."""
        has_selection = len(self.selected_images) > 0
        self.delete_selected_btn.Enable(has_selection)

    def _add_image_preview(self, chat_image: ChatImage) -> None:
        """Add an image preview to the preview area."""
        try:
            # Create selectable image panel
            img_panel = SelectableImagePanel(
                self.image_container, 
                chat_image, 
                self._on_image_selection_changed
            )
            
            # Track the panel
            self.image_panels.append(img_panel)
            
            # Add to main image sizer
            self.image_sizer.Add(img_panel, 0, wx.ALL, 5)
            
            # Update layout
            self.image_container.Layout()
            self.image_scroll.FitInside()
            self.Layout()
            
        except Exception as e:
            logger.error(f"Error in _add_image_preview for {chat_image.filename}: {e}")

    def _on_image_selection_changed(self, chat_image: ChatImage, selected: bool) -> None:
        """Handle selection change of an image."""
        if selected:
            if chat_image not in self.selected_images:
                self.selected_images.append(chat_image)
        else:
            if chat_image in self.selected_images:
                self.selected_images.remove(chat_image)
        
        self._update_delete_button_state()

    def _remove_image_preview(self, img_panel: SelectableImagePanel, chat_image: ChatImage) -> None:
        """Remove an image preview."""
        try:
            # Remove from attached images list
            if chat_image in self.attached_images:
                self.attached_images.remove(chat_image)
            
            # Remove from selection list
            if chat_image in self.selected_images:
                self.selected_images.remove(chat_image)
            
            # Remove from tracking list
            if img_panel in self.image_panels:
                self.image_panels.remove(img_panel)
            
            # Remove from sizer and destroy panel
            self.image_sizer.Detach(img_panel)
            img_panel.Destroy()
            
            # Update layout
            self.image_container.Layout()
            self.image_scroll.FitInside()
            self.Layout()
            
            logger.info(f"Removed image: {chat_image.filename}")
            
            # Update delete button state
            self._update_delete_button_state()
            
            # Notify callback
            if self.on_images_changed:
                self.on_images_changed(self.attached_images)
                
        except Exception as e:
            logger.error(f"Error removing image preview: {e}")

    def _clear_attached_images(self) -> None:
        """Clear all attached images."""
        try:
            # Clear the lists
            self.attached_images.clear()
            self.selected_images.clear()
            self.image_panels.clear()
            
            # Remove all children from the sizer
            sizer_count = self.image_sizer.GetItemCount()
            
            for i in range(sizer_count - 1, -1, -1):
                sizer_item = self.image_sizer.GetItem(i)
                if sizer_item and sizer_item.GetWindow():
                    window = sizer_item.GetWindow()
                    self.image_sizer.Detach(window)
                    window.Destroy()
            
            # Update layout
            self.image_container.Layout()
            self.image_scroll.FitInside()
            self.Layout()
            
            # Update delete button state
            self._update_delete_button_state()
            
            # Notify callback
            if self.on_images_changed:
                self.on_images_changed(self.attached_images)
                
        except Exception as e:
            logger.error(f"Error clearing attached images: {e}")

    def _show_image_viewer(self, chat_image: ChatImage) -> None:
        """Show the image viewer dialog."""
        dialog = ImageViewerDialog(self, chat_image)
        dialog.ShowModal()
        dialog.Destroy()

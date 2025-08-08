"""
Selectable image panel component for displaying images with selection support.
"""

import wx
import os
import base64
import tempfile
import logging
from typing import Callable, Optional

from llamalot.models.chat import ChatImage
from llamalot.utils.logging_config import get_logger

logger = get_logger(__name__)


class SelectableImagePanel(wx.Panel):
    """A panel that displays an image and can be selected."""
    
    def __init__(self, parent: wx.Window, chat_image: ChatImage, on_selection_change: Callable[[ChatImage, bool], None]):
        """
        Initialize the selectable image panel.
        
        Args:
            parent: Parent window
            chat_image: The ChatImage to display
            on_selection_change: Callback for selection state changes
        """
        super().__init__(parent)
        self.chat_image = chat_image
        self.on_selection_change = on_selection_change
        self.selected = False
        self.bitmap: Optional[wx.Bitmap] = None
        
        self.SetBackgroundColour(wx.Colour(240, 240, 240))
        self._create_ui()
        self._bind_events()
    
    def _create_ui(self) -> None:
        """Create the UI for this image panel."""
        # Create vertical sizer for the image panel
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Try to create a preview image
        try:
            self._create_image_preview()
        except Exception as e:
            logger.error(f"Error creating image preview: {e}")
            # Show placeholder on error
            placeholder = wx.StaticText(self, label="Image")
            self.sizer.Add(placeholder, 0, wx.ALL | wx.CENTER, 2)
        
        # Add labels and controls
        self._create_labels_and_controls()
        
        self.SetSizer(self.sizer)
        
    def _create_image_preview(self) -> None:
        """Create the image preview control."""
        # Decode image data
        image_data = base64.b64decode(self.chat_image.data)
        
        # Save to temporary file and load
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            temp_file.write(image_data)
            temp_path = temp_file.name
        
        try:
            # Create wx.Image from file
            wx_image = wx.Image(temp_path, wx.BITMAP_TYPE_ANY)
            
            if wx_image.IsOk():
                # Scale to preview size (100x100 max, maintaining aspect ratio)
                original_w, original_h = wx_image.GetSize()
                scale_factor = min(100.0 / original_w, 100.0 / original_h)
                new_w = int(original_w * scale_factor)
                new_h = int(original_h * scale_factor)
                
                # Scale the image
                scaled_image = wx_image.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
                self.bitmap = wx.Bitmap(scaled_image)
                
                # Create panel to display the image
                self.img_ctrl = wx.Panel(self)
                self.img_ctrl.SetMinSize(wx.Size(new_w, new_h))
                self.img_ctrl.SetSize(wx.Size(new_w, new_h))
                
                # Paint event to draw the image
                self.img_ctrl.Bind(wx.EVT_PAINT, self._on_image_paint)
                self.img_ctrl.Bind(wx.EVT_LEFT_UP, self._on_image_click)
                self.img_ctrl.Bind(wx.EVT_LEFT_DCLICK, self._on_image_double_click)
                
                self.sizer.Add(self.img_ctrl, 0, wx.ALL | wx.CENTER, 2)
                
            else:
                # Image loading failed, show placeholder
                placeholder = wx.StaticText(self, label="Image")
                self.sizer.Add(placeholder, 0, wx.ALL | wx.CENTER, 2)
                
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {temp_path}: {e}")
                
    def _create_labels_and_controls(self) -> None:
        """Create the filename label, size label, and remove button."""
        # Filename label (truncated if too long)
        filename = self.chat_image.filename or "Unknown"
        if len(filename) > 15:
            filename = filename[:12] + "..."
        self.filename_label = wx.StaticText(self, label=filename)
        self.filename_label.SetFont(self.filename_label.GetFont().Smaller())
        
        # Size label
        size_text = f"{(self.chat_image.size or 0) / 1024:.1f} KB"
        self.size_label = wx.StaticText(self, label=size_text)
        self.size_label.SetFont(self.size_label.GetFont().Smaller())
        
        # Remove button
        self.remove_btn = wx.Button(self, label="✕", size=wx.Size(20, 20))
        self.remove_btn.SetFont(self.remove_btn.GetFont().Smaller())
        
        # Add to sizer
        self.sizer.Add(self.filename_label, 0, wx.ALL | wx.CENTER, 1)
        self.sizer.Add(self.size_label, 0, wx.ALL | wx.CENTER, 1)
        self.sizer.Add(self.remove_btn, 0, wx.ALL | wx.CENTER, 1)
        
    def _bind_events(self) -> None:
        """Bind panel events."""
        self.remove_btn.Bind(wx.EVT_BUTTON, self._on_remove)
        self.Bind(wx.EVT_LEFT_UP, self._on_panel_click)
        
    def _on_image_paint(self, event: wx.PaintEvent) -> None:
        """Paint the image on the image control."""
        dc = wx.PaintDC(event.GetEventObject())
        if self.bitmap and self.bitmap.IsOk():
            dc.DrawBitmap(self.bitmap, 0, 0)
            
    def _on_image_click(self, event: wx.MouseEvent) -> None:
        """Handle single click on image."""
        self.toggle_selection()
        event.Skip()
        
    def _on_panel_click(self, event: wx.MouseEvent) -> None:
        """Handle click on panel (outside image)."""
        self.toggle_selection()
        event.Skip()
        
    def _on_image_double_click(self, event: wx.MouseEvent) -> None:
        """Handle double-click on image."""
        # Get parent panel to show image viewer
        parent = self.GetParent()
        while parent and not hasattr(parent, '_show_image_viewer'):
            parent = parent.GetParent()
        if parent:
            parent._show_image_viewer(self.chat_image)  # type: ignore
        event.Skip()
        
    def _on_remove(self, event: wx.CommandEvent) -> None:
        """Handle remove button click."""
        # Get parent panel to handle removal
        parent = self.GetParent()
        while parent and not hasattr(parent, '_remove_image_preview'):
            parent = parent.GetParent()
        if parent:
            parent._remove_image_preview(self, self.chat_image)  # type: ignore
        
    def toggle_selection(self) -> None:
        """Toggle selection state of this image."""
        self.set_selected(not self.selected)
        
    def set_selected(self, selected: bool) -> None:
        """Set selection state and update visual appearance."""
        self.selected = selected
        
        # Update visual appearance
        if self.selected:
            self.SetBackgroundColour(wx.Colour(173, 216, 230))  # Light blue
        else:
            self.SetBackgroundColour(wx.Colour(240, 240, 240))  # Light gray
            
        self.Refresh()
        
        # Notify parent of selection change
        self.on_selection_change(self.chat_image, self.selected)

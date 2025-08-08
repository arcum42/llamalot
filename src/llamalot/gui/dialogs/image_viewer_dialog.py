"""
Image viewer dialog for displaying images in full size.

Provides functionality for viewing attached images with clipboard copy support.
"""

import wx
import os
import base64
import tempfile
import logging
from typing import Optional

from llamalot.models.chat import ChatImage
from llamalot.utils.logging_config import get_logger

logger = get_logger(__name__)


class ImageDisplayPanel(wx.Panel):
    """Panel that displays an image with clipboard support."""
    
    def __init__(self, parent: wx.Window, bitmap: wx.Bitmap, chat_image: ChatImage):
        """Initialize the image display panel."""
        super().__init__(parent)
        
        self.bitmap = bitmap
        self.chat_image = chat_image
        
        # Set size to match bitmap
        self.SetMinSize(wx.Size(bitmap.GetWidth(), bitmap.GetHeight()))
        self.SetSize(wx.Size(bitmap.GetWidth(), bitmap.GetHeight()))


class ImageViewerDialog(wx.Dialog):
    """Dialog for viewing images in full size with clipboard support."""
    
    def __init__(self, parent: wx.Window, chat_image: ChatImage):
        """
        Initialize the image viewer dialog.
        
        Args:
            parent: Parent window
            chat_image: The ChatImage to display
        """
        super().__init__(
            parent, 
            title=f"Image Viewer - {chat_image.filename or 'Unknown'}", 
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX
        )
        
        self.chat_image = chat_image
        self.SetMinSize(wx.Size(400, 300))
        self.restore_timer: Optional[wx.CallLater] = None
        
        self._create_ui()
        self._bind_events()
        
    def _create_ui(self) -> None:
        """Create the user interface."""
        # Create layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create scrolled window for the image
        scroll_window = wx.ScrolledWindow(self)
        scroll_window.SetScrollRate(20, 20)
        scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Try to load and display the image
        try:
            image_ctrl = self._create_image_control(scroll_window)
            if image_ctrl:
                scroll_sizer.Add(image_ctrl, 0, wx.ALL | wx.CENTER, 10)
            else:
                self._add_error_message(scroll_window, scroll_sizer, "Failed to load image")
                
        except Exception as e:
            logger.error(f"Error displaying image in viewer: {e}")
            self._add_error_message(scroll_window, scroll_sizer, f"Error loading image: {str(e)}")
        
        scroll_window.SetSizer(scroll_sizer)
        main_sizer.Add(scroll_window, 1, wx.EXPAND | wx.ALL, 5)
        
        # Add close button
        self._add_close_button(main_sizer)
        
        self.SetSizer(main_sizer)
        
    def _create_image_control(self, parent: wx.Window) -> Optional[ImageDisplayPanel]:
        """Create the image display control."""
        # Decode image data
        image_data = base64.b64decode(self.chat_image.data)
        
        # Save to temporary file and load
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            temp_file.write(image_data)
            temp_path = temp_file.name
        
        try:
            # Create wx.Image from file
            wx_image = wx.Image(temp_path, wx.BITMAP_TYPE_ANY)
            
            if not wx_image.IsOk():
                return None
                
            # Get original size
            original_w, original_h = wx_image.GetSize()
            
            # Create custom panel to display the image
            bitmap = wx.Bitmap(wx_image)
            image_ctrl = ImageDisplayPanel(parent, bitmap, self.chat_image)
            
            # Bind events
            image_ctrl.Bind(wx.EVT_PAINT, self._on_image_paint)
            image_ctrl.Bind(wx.EVT_RIGHT_UP, self._on_right_click)
            image_ctrl.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
            
            # Make sure the panel can receive keyboard focus
            image_ctrl.SetCanFocus(True)
            
            # Set dialog size based on image size (with reasonable limits)
            display_w = min(original_w + 40, 1200)  # Max width 1200
            display_h = min(original_h + 100, 800)  # Max height 800
            self.SetSize(wx.Size(display_w, display_h))
            self.Center()
            
            return image_ctrl
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
                
    def _add_error_message(self, parent: wx.Window, sizer: wx.BoxSizer, message: str) -> None:
        """Add an error message to the interface."""
        error_text = wx.StaticText(parent, label=message)
        sizer.Add(error_text, 0, wx.ALL | wx.CENTER, 20)
        
    def _add_close_button(self, main_sizer: wx.BoxSizer) -> None:
        """Add the close button to the interface."""
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        close_btn = wx.Button(self, wx.ID_CLOSE, "Close")
        close_btn.Bind(wx.EVT_BUTTON, self._on_close)
        btn_sizer.Add(close_btn, 0, wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        
    def _bind_events(self) -> None:
        """Bind dialog events."""
        self.Bind(wx.EVT_CLOSE, self._on_close)
        
    def _on_image_paint(self, event: wx.PaintEvent) -> None:
        """Handle image paint event."""
        panel = event.GetEventObject()
        if isinstance(panel, ImageDisplayPanel):
            dc = wx.PaintDC(panel)
            if panel.bitmap.IsOk():
                dc.DrawBitmap(panel.bitmap, 0, 0)
            
    def _on_right_click(self, event: wx.MouseEvent) -> None:
        """Handle right-click on image."""
        panel = event.GetEventObject()
        if isinstance(panel, ImageDisplayPanel):
            self._show_context_menu(panel, event.GetPosition())
        
    def _on_key_down(self, event: wx.KeyEvent) -> None:
        """Handle keyboard shortcuts."""
        if event.GetKeyCode() == ord('C') and event.ControlDown():
            panel = event.GetEventObject()
            if isinstance(panel, ImageDisplayPanel):
                self._copy_image_to_clipboard(panel)
        else:
            event.Skip()
            
    def _show_context_menu(self, panel: ImageDisplayPanel, position: wx.Point) -> None:
        """Show context menu with copy option."""
        menu = wx.Menu()
        
        # Add copy to clipboard option with keyboard shortcut hint
        copy_item = menu.Append(wx.ID_COPY, "Copy Image to Clipboard\tCtrl+C")
        
        # Bind menu events
        def on_copy(event):
            self._copy_image_to_clipboard(panel)
        
        self.Bind(wx.EVT_MENU, on_copy, copy_item)
        
        # Show menu at cursor position
        panel.PopupMenu(menu, position)
        menu.Destroy()
    
    def _copy_image_to_clipboard(self, panel: ImageDisplayPanel) -> None:
        """Copy the image to the clipboard."""
        try:
            if not panel.bitmap.IsOk():
                wx.MessageBox("No image to copy", "Error", wx.OK | wx.ICON_ERROR)
                return
                
            # Get the clipboard
            if not wx.TheClipboard.Open():
                wx.MessageBox("Unable to access clipboard", "Error", wx.OK | wx.ICON_ERROR)
                return
                
            try:
                # Create bitmap data object
                bitmap_data = wx.BitmapDataObject(panel.bitmap)
                
                # Clear clipboard and set new data
                wx.TheClipboard.Clear()
                wx.TheClipboard.SetData(bitmap_data)
                
                # Log success
                logger.info("Image copied to clipboard successfully")
                
                # Show brief success message in title bar
                self._show_success_message()
                
            finally:
                wx.TheClipboard.Close()
                
        except Exception as e:
            logger.error(f"Error copying image to clipboard: {e}")
            wx.MessageBox(f"Error copying image: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
            
    def _show_success_message(self) -> None:
        """Show success message in title bar temporarily."""
        original_title = self.GetTitle()
        self.SetTitle(f"{original_title} - Image copied to clipboard!")
        
        # Cancel any existing timer
        if self.restore_timer:
            self.restore_timer.Stop()
        
        # Restore original title after 2 seconds (only if dialog still exists)
        def restore_title():
            try:
                # Check if the dialog still exists and is valid
                if self and not self.IsBeingDeleted():
                    self.SetTitle(original_title)
                    self.restore_timer = None
            except RuntimeError:
                # Dialog has been destroyed, ignore
                pass
        
        self.restore_timer = wx.CallLater(2000, restore_title)
        
    def _on_close(self, event: wx.CloseEvent) -> None:
        """Handle close event."""
        # Cancel any pending title restore timer
        if self.restore_timer:
            self.restore_timer.Stop()
            self.restore_timer = None
        
        self.EndModal(wx.ID_CLOSE)

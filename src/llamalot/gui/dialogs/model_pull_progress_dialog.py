"""
Model pull progress dialog for tracking Ollama model downloads.
"""

import wx
import logging
from typing import Dict, Any

from llamalot.utils.logging_config import get_logger

logger = get_logger(__name__)


class ModelPullProgressDialog(wx.Dialog):
    """Dialog for showing model pull progress with streaming updates."""
    
    def __init__(self, parent: wx.Window, model_name: str):
        """
        Initialize the model pull progress dialog.
        
        Args:
            parent: Parent window
            model_name: Name of the model being pulled
        """
        super().__init__(
            parent, 
            title=f"Pulling Model: {model_name}", 
            size=wx.Size(400, 200),
            style=wx.DEFAULT_DIALOG_STYLE
        )
        
        self.model_name = model_name
        self.cancelled = False
        
        self._create_ui()
        self._bind_events()
        
    def _create_ui(self) -> None:
        """Create the user interface."""
        # Create layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Model name label
        name_label = wx.StaticText(self, label=f"Downloading: {self.model_name}")
        name_label.SetFont(name_label.GetFont().Bold())
        main_sizer.Add(name_label, 0, wx.ALL | wx.CENTER, 10)
        
        # Progress bar
        self.progress_bar = wx.Gauge(self, range=100, size=wx.Size(350, 25))
        main_sizer.Add(self.progress_bar, 0, wx.ALL | wx.EXPAND, 10)
        
        # Status text
        self.status_text = wx.StaticText(self, label="Initializing download...")
        main_sizer.Add(self.status_text, 0, wx.ALL | wx.CENTER, 5)
        
        # Progress details text
        self.details_text = wx.StaticText(self, label="")
        main_sizer.Add(self.details_text, 0, wx.ALL | wx.CENTER, 5)
        
        # Cancel button
        self.cancel_btn = wx.Button(self, wx.ID_CANCEL, "Cancel Download")
        self.cancel_btn.SetForegroundColour(wx.Colour(128, 0, 0))  # Dark red text
        main_sizer.Add(self.cancel_btn, 0, wx.ALL | wx.CENTER, 10)
        
        self.SetSizer(main_sizer)
        self.CenterOnParent()
        
    def _bind_events(self) -> None:
        """Bind dialog events."""
        self.Bind(wx.EVT_BUTTON, self._on_cancel, self.cancel_btn)
        self.Bind(wx.EVT_CLOSE, self._on_close)
    
    def update_progress(self, status: str, data: Dict[str, Any]) -> None:
        """
        Update progress bar and status text from streaming data.
        
        Args:
            status: Status message
            data: Progress data dictionary
        """
        try:
            # Extract progress information from the streaming response
            if 'status' in data:
                status_msg = data['status']
                self.status_text.SetLabel(status_msg)
            
            # Handle different progress phases
            if 'total' in data and 'completed' in data and data['total'] > 0:
                # Calculate percentage
                progress = int((data['completed'] / data['total']) * 100)
                self.progress_bar.SetValue(progress)
                
                # Format size information
                total_mb = data['total'] / (1024 * 1024)
                completed_mb = data['completed'] / (1024 * 1024)
                self.details_text.SetLabel(f"{completed_mb:.1f} MB / {total_mb:.1f} MB")
            
            elif 'digest' in data:
                # Show digest info for verification phase
                digest = data['digest']
                if len(digest) > 16:
                    digest = digest[:16] + "..."
                self.details_text.SetLabel(f"Digest: {digest}")
            
            # Force refresh
            self.Layout()
            wx.GetApp().Yield()
            
        except Exception as e:
            logger.warning(f"Error updating progress: {e}")
    
    def _on_cancel(self, event: wx.CommandEvent) -> None:
        """Handle cancel button."""
        if not self.cancelled:
            self.cancelled = True
            # Update UI to show cancellation in progress
            self.status_text.SetLabel("Cancelling download...")
            self.details_text.SetLabel("Please wait while the download is cancelled...")
            self.cancel_btn.Enable(False)  # Disable button to prevent multiple clicks
            self.Layout()
            logger.info(f"User requested cancellation of model pull: {self.model_name}")
        
        # Don't end modal here - let the worker thread handle it
    
    def _on_close(self, event: wx.CloseEvent) -> None:
        """Handle dialog close."""
        self.cancelled = True
        event.Skip()
    
    def is_cancelled(self) -> bool:
        """
        Check if the download was cancelled.
        
        Returns:
            True if cancelled, False otherwise
        """
        return self.cancelled

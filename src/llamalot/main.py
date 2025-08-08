#!/usr/bin/env python3
"""
Main module for LlamaLot application.

Contains the main function and application initialization logic.
"""

import wx
import sys
import logging
from typing import Optional

from llamalot.gui.main_window import MainWindow
from llamalot.gui.windows.enhanced_main_window import EnhancedMainWindow
from llamalot.utils.logging_config import setup_logging


class LlamaLotApp(wx.App):
    """Main wxPython application class for LlamaLot."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_window: Optional[wx.Frame] = None
    
    def OnInit(self) -> bool:
        """Initialize the application."""
        try:
            # Set up logging
            setup_logging()
            logging.info("Starting LlamaLot application")
            
            # Create and show the enhanced main window
            self.main_window = EnhancedMainWindow()
            self.main_window.Show()
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize application: {e}")
            wx.MessageBox(
                f"Failed to start LlamaLot:\n{str(e)}", 
                "Startup Error", 
                wx.OK | wx.ICON_ERROR
            )
            return False
    
    def OnExit(self) -> int:
        """Clean up when the application exits."""
        logging.info("LlamaLot application exiting")
        return super().OnExit()


def main() -> None:
    """Main entry point for the application."""
    # Create and run the wxPython application
    app = LlamaLotApp()
    app.MainLoop()


if __name__ == "__main__":
    main()

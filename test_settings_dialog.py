#!/usr/bin/env python3
"""
Quick test for the Settings dialog layout.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import wx
from llamalot.gui.dialogs.settings_dialog import SettingsDialog
from llamalot.models.config import ApplicationConfig

class TestApp(wx.App):
    def OnInit(self):
        # Create a dummy config and model list
        config = ApplicationConfig()
        available_models = ["llama3:8b", "gemma:7b", "mistral:7b", "codellama:13b"]
        
        # Create and show the settings dialog
        with SettingsDialog(None, config, available_models) as dialog:
            result = dialog.ShowModal()
            if result == wx.ID_OK:
                print("Settings dialog closed with OK")
            else:
                print("Settings dialog closed with Cancel")
        
        return False  # Exit immediately after showing dialog

if __name__ == "__main__":
    app = TestApp()
    app.MainLoop()

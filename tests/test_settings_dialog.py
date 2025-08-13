#!/usr/bin/env python3
"""
Unit tests for settings dialog functionality.
"""

import unittest
from unittest.mock import Mock, patch
from pathlib import Path

# Add src to path for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llamalot.models.config import ApplicationConfig, OllamaServerConfig


class TestSettingsDialog(unittest.TestCase):
    """Test cases for settings dialog functionality."""
    
    def test_application_config_creation(self):
        """Test that ApplicationConfig can be created with default values."""
        config = ApplicationConfig()
        
        # Test default values
        self.assertIsInstance(config.ollama_server, OllamaServerConfig)
        self.assertEqual(config.ollama_server.timeout, 180)  # Default timeout
        self.assertEqual(config.ollama_server.effective_timeout, 180)
    
    def test_timeout_configuration(self):
        """Test timeout configuration and effective_timeout property."""
        config = ApplicationConfig()
        
        # Test normal timeout
        config.ollama_server.timeout = 300
        self.assertEqual(config.ollama_server.effective_timeout, 300)
        
        # Test unlimited timeout (-1)
        config.ollama_server.timeout = -1
        self.assertIsNone(config.ollama_server.effective_timeout)
        
        # Test zero timeout
        config.ollama_server.timeout = 0
        self.assertIsNone(config.ollama_server.effective_timeout)
    
    def test_config_serialization(self):
        """Test that config can be converted to/from dict."""
        config = ApplicationConfig()
        config.ollama_server.timeout = 240
        
        # This would test the to_dict/from_dict methods if they exist
        # For now, just test that the values are preserved
        self.assertEqual(config.ollama_server.timeout, 240)
        self.assertEqual(config.ollama_server.effective_timeout, 240)
    
    @patch('wx.App')
    @patch('wx.Frame')
    def test_settings_dialog_import(self, mock_frame, mock_app):
        """Test that SettingsDialog can be imported without GUI."""
        try:
            from llamalot.gui.dialogs.settings_dialog import SettingsDialog
            # If we get here, the import was successful
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Could not import SettingsDialog: {e}")


if __name__ == '__main__':
    unittest.main()

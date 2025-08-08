"""
Tests for configuration management functionality.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from llamalot.backend.config import ConfigurationManager, get_config_manager, get_config
from llamalot.models import ApplicationConfig


class TestConfigurationManager(unittest.TestCase):
    """Test cases for ConfigurationManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"
        self.manager = ConfigurationManager(self.config_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test configuration manager initialization."""
        self.assertEqual(self.manager.config_path, self.config_path)
        self.assertIsNone(self.manager._config)
        self.assertFalse(self.manager._loaded)
    
    def test_load_default_config(self):
        """Test loading default configuration when file doesn't exist."""
        config = self.manager.load()
        
        self.assertIsInstance(config, ApplicationConfig)
        self.assertTrue(self.manager._loaded)
        self.assertIsNotNone(self.manager._config)
    
    def test_load_existing_config(self):
        """Test loading configuration from existing file."""
        # Create a test config file
        test_config = ApplicationConfig()
        test_config.ollama_server.host = "test.example.com"
        test_config.save_to_file(self.config_path)
        
        # Load the configuration
        config = self.manager.load()
        
        self.assertEqual(config.ollama_server.host, "test.example.com")
        self.assertTrue(self.manager._loaded)
    
    def test_config_property_lazy_loading(self):
        """Test that config property loads configuration lazily."""
        # Access config property - should trigger loading
        config = self.manager.config
        
        self.assertIsInstance(config, ApplicationConfig)
        self.assertTrue(self.manager._loaded)
    
    def test_save_config(self):
        """Test saving configuration to file."""
        # Load and modify config
        config = self.manager.config
        config.ollama_server.host = "saved.example.com"
        
        # Save configuration
        result = self.manager.save()
        
        self.assertTrue(result)
        self.assertTrue(self.config_path.exists())
        
        # Verify saved content
        new_manager = ConfigurationManager(self.config_path)
        loaded_config = new_manager.load()
        self.assertEqual(loaded_config.ollama_server.host, "saved.example.com")
    
    def test_save_without_loaded_config(self):
        """Test saving when no configuration is loaded."""
        result = self.manager.save()
        self.assertFalse(result)
    
    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        # Load and modify config
        config = self.manager.config
        config.ollama_server.host = "modified.example.com"
        
        # Reset to defaults
        reset_config = self.manager.reset_to_defaults()
        
        self.assertIsInstance(reset_config, ApplicationConfig)
        self.assertEqual(reset_config.ollama_server.host, "localhost")
        self.assertTrue(self.manager._loaded)
    
    def test_update_ollama_server(self):
        """Test updating Ollama server configuration."""
        self.manager.update_ollama_server(
            host="test.server.com",
            port=11434,
            use_https=True,
            timeout=60
        )
        
        config = self.manager.config
        self.assertEqual(config.ollama_server.host, "test.server.com")
        self.assertEqual(config.ollama_server.port, 11434)
        self.assertTrue(config.ollama_server.use_https)
        self.assertEqual(config.ollama_server.timeout, 60)
    
    def test_update_ui_preferences(self):
        """Test updating UI preferences."""
        self.manager.update_ui_preferences(
            window_width=1200,
            window_height=800,
            theme="dark"
        )
        
        config = self.manager.config
        self.assertEqual(config.ui_preferences.window_width, 1200)
        self.assertEqual(config.ui_preferences.window_height, 800)
        self.assertEqual(config.ui_preferences.theme, "dark")
    
    def test_update_ui_preferences_invalid_field(self):
        """Test updating UI preferences with invalid field."""
        with patch('llamalot.backend.config.logger') as mock_logger:
            self.manager.update_ui_preferences(invalid_field="value")
            mock_logger.warning.assert_called_with("Unknown UI preference: invalid_field")
    
    def test_update_chat_defaults(self):
        """Test updating chat default settings."""
        self.manager.update_chat_defaults(
            temperature=0.8,
            context_length=2048,
            top_p=0.9
        )
        
        config = self.manager.config
        self.assertEqual(config.chat_defaults.temperature, 0.8)
        self.assertEqual(config.chat_defaults.context_length, 2048)
        self.assertEqual(config.chat_defaults.top_p, 0.9)
    
    def test_mark_first_run_complete(self):
        """Test marking first run as complete."""
        config = self.manager.config
        config.first_run = True
        
        self.manager.mark_first_run_complete()
        
        self.assertFalse(config.first_run)
    
    def test_update_last_model_refresh(self):
        """Test updating last model refresh timestamp."""
        self.manager.update_last_model_refresh()
        
        config = self.manager.config
        self.assertIsNotNone(config.last_model_refresh)
    
    def test_get_directory_methods(self):
        """Test directory path getter methods."""
        config = self.manager.config
        
        # Ensure directories are configured
        config.data_directory = "/test/data"
        config.cache_directory = "/test/cache"
        config.logs_directory = "/test/logs"
        config.database_file = "/test/db.sqlite"
        
        self.assertEqual(self.manager.get_data_directory(), Path("/test/data"))
        self.assertEqual(self.manager.get_cache_directory(), Path("/test/cache"))
        self.assertEqual(self.manager.get_logs_directory(), Path("/test/logs"))
        self.assertEqual(self.manager.get_database_path(), Path("/test/db.sqlite"))
    
    def test_get_directory_methods_unconfigured(self):
        """Test directory path getters when directories are not configured."""
        config = self.manager.config
        config.data_directory = None
        
        with self.assertRaises(ValueError):
            self.manager.get_data_directory()
    
    def test_export_config(self):
        """Test exporting configuration to file."""
        export_path = Path(self.temp_dir) / "exported_config.json"
        
        # Modify config
        config = self.manager.config
        config.ollama_server.host = "export.test.com"
        
        # Export configuration
        result = self.manager.export_config(export_path)
        
        self.assertTrue(result)
        self.assertTrue(export_path.exists())
        
        # Verify exported content
        with open(export_path, 'r') as f:
            exported_data = json.load(f)
        
        self.assertEqual(exported_data['ollama_server']['host'], "export.test.com")
    
    def test_import_config(self):
        """Test importing configuration from file."""
        import_path = Path(self.temp_dir) / "import_config.json"
        
        # Create test import file
        test_data = {
            "ollama_server": {
                "host": "import.test.com",
                "port": 11434,
                "use_https": False,
                "timeout": 30
            },
            "ui_preferences": {
                "window_width": 1024,
                "window_height": 768,
                "theme": "light"
            },
            "chat_defaults": {
                "temperature": 0.7,
                "max_tokens": 1024,
                "top_p": 1.0,
                "stream": True
            },
            "first_run": False,
            "last_model_refresh": None
        }
        
        with open(import_path, 'w') as f:
            json.dump(test_data, f)
        
        # Import configuration
        result = self.manager.import_config(import_path)
        
        self.assertTrue(result)
        
        config = self.manager.config
        self.assertEqual(config.ollama_server.host, "import.test.com")
        self.assertEqual(config.ui_preferences.window_width, 1024)
        self.assertEqual(config.chat_defaults.temperature, 0.7)
    
    def test_validate_config_valid(self):
        """Test configuration validation with valid config."""
        config = self.manager.config
        config.data_directory = self.temp_dir  # Use existing temp directory
        
        results = self.manager.validate_config()
        
        self.assertTrue(results['valid'])
        self.assertEqual(len(results['errors']), 0)
    
    def test_validate_config_invalid(self):
        """Test configuration validation with invalid config."""
        config = self.manager.config
        config.ollama_server.host = ""  # Invalid empty host
        config.ollama_server.port = -1  # Invalid port
        config.chat_defaults.temperature = 5.0  # Out of normal range
        
        results = self.manager.validate_config()
        
        self.assertFalse(results['valid'])
        self.assertGreater(len(results['errors']), 0)
        self.assertGreater(len(results['warnings']), 0)
    
    def test_str_representation(self):
        """Test string representation of configuration manager."""
        str_repr = str(self.manager)
        self.assertIn("ConfigurationManager", str_repr)
        self.assertIn(str(self.config_path), str_repr)
        self.assertIn("loaded=False", str_repr)


class TestGlobalConfigManager(unittest.TestCase):
    """Test cases for global configuration manager functions."""
    
    def test_get_config_manager_singleton(self):
        """Test that get_config_manager returns singleton instance."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        
        self.assertIs(manager1, manager2)
        self.assertIsInstance(manager1, ConfigurationManager)
    
    def test_get_config(self):
        """Test get_config convenience function."""
        config = get_config()
        
        self.assertIsInstance(config, ApplicationConfig)
    
    @patch('llamalot.backend.config._config_manager', None)
    def test_get_config_manager_fresh_instance(self):
        """Test getting fresh configuration manager instance."""
        # Reset global instance
        import llamalot.backend.config
        llamalot.backend.config._config_manager = None
        
        manager = get_config_manager()
        
        self.assertIsInstance(manager, ConfigurationManager)


if __name__ == '__main__':
    unittest.main()

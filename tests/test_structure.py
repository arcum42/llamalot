"""
Basic tests for LlamaLot application structure.
"""

import sys
import os
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestProjectStructure(unittest.TestCase):
    """Test that the project structure is set up correctly."""
    
    def setUp(self):
        """Set up test paths."""
        self.project_root = Path(__file__).parent.parent
        self.src_dir = self.project_root / "src"
        self.llamalot_dir = self.src_dir / "llamalot"
    
    def test_project_directories_exist(self):
        """Test that all required directories exist."""
        required_dirs = [
            self.src_dir,
            self.llamalot_dir,
            self.llamalot_dir / "gui",
            self.llamalot_dir / "backend", 
            self.llamalot_dir / "models",
            self.llamalot_dir / "utils",
        ]
        
        for dir_path in required_dirs:
            with self.subTest(directory=str(dir_path)):
                self.assertTrue(dir_path.exists(), f"Directory {dir_path} does not exist")
                self.assertTrue(dir_path.is_dir(), f"{dir_path} is not a directory")
    
    def test_init_files_exist(self):
        """Test that all __init__.py files exist."""
        required_init_files = [
            self.llamalot_dir / "__init__.py",
            self.llamalot_dir / "gui" / "__init__.py",
            self.llamalot_dir / "backend" / "__init__.py",
            self.llamalot_dir / "models" / "__init__.py",
            self.llamalot_dir / "utils" / "__init__.py",
        ]
        
        for init_file in required_init_files:
            with self.subTest(init_file=str(init_file)):
                self.assertTrue(init_file.exists(), f"__init__.py file {init_file} does not exist")
                self.assertTrue(init_file.is_file(), f"{init_file} is not a file")
    
    def test_main_files_exist(self):
        """Test that main files exist."""
        required_files = [
            self.project_root / "main.py",
            self.llamalot_dir / "main.py",
            self.llamalot_dir / "gui" / "main_window.py",
            self.llamalot_dir / "utils" / "logging_config.py",
        ]
        
        for file_path in required_files:
            with self.subTest(file=str(file_path)):
                self.assertTrue(file_path.exists(), f"File {file_path} does not exist")
                self.assertTrue(file_path.is_file(), f"{file_path} is not a file")
    
    def test_import_main_module(self):
        """Test that the main module can be imported."""
        try:
            from llamalot import main
            self.assertTrue(hasattr(main, 'main'), "main module should have a main function")
        except ImportError as e:
            self.fail(f"Could not import llamalot.main: {e}")
    
    def test_import_utils(self):
        """Test that utility modules can be imported."""
        try:
            from llamalot.utils import logging_config
            self.assertTrue(hasattr(logging_config, 'setup_logging'), 
                          "logging_config should have setup_logging function")
        except ImportError as e:
            self.fail(f"Could not import llamalot.utils.logging_config: {e}")


if __name__ == "__main__":
    unittest.main()

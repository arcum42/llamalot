"""
Tests for the prompts system including data models and manager functionality.
"""

import unittest
import tempfile
import shutil
import json
import os
from pathlib import Path

from llamalot.models.prompts import BasePrompt, ExtraPrompt, PromptsConfig
from llamalot.backend.prompts_manager import PromptsManager


class TestPromptsModels(unittest.TestCase):
    """Test prompts data models."""
    
    def test_base_prompt_creation(self):
        """Test BasePrompt creation."""
        prompt = BasePrompt(
            id="test1",
            name="Test Prompt",
            category="testing",
            input_type="text",
            prompt="This is a test prompt."
        )
        
        self.assertEqual(prompt.name, "Test Prompt")
        self.assertEqual(prompt.category, "testing")
        self.assertEqual(prompt.input_type, "text")
        self.assertEqual(prompt.id, "test1")
    
    def test_extra_prompt_creation(self):
        """Test ExtraPrompt creation."""
        prompt = ExtraPrompt(
            id="extra1",
            name="Extra Test",
            category="testing",
            type="boolean",
            prompt="Add extra detail.",
            default=True
        )
        
        self.assertEqual(prompt.type, "boolean")
        self.assertTrue(prompt.default)
        
        # Test wildcard type
        wildcard_prompt = ExtraPrompt(
            id="extra2",
            name="Wildcard Test",
            category="testing",
            type="wildcard",
            prompt="Add {value} to the description."
        )
        
        self.assertEqual(wildcard_prompt.type, "wildcard")
        self.assertIsNone(wildcard_prompt.default)
    
    def test_prompts_config(self):
        """Test PromptsConfig container."""
        base_prompt = BasePrompt(
            id="base1",
            name="Base Test",
            category="test",
            input_type="text",
            prompt="Base prompt"
        )
        
        extra_prompt = ExtraPrompt(
            id="extra1",
            name="Extra Test",
            category="test",
            type="boolean",
            prompt="Extra prompt"
        )
        
        config = PromptsConfig(
            base_prompts={"base1": base_prompt},
            extra_prompts={"extra1": extra_prompt}
        )
        
        self.assertEqual(len(config.base_prompts), 1)
        self.assertEqual(len(config.extra_prompts), 1)


class TestPromptsManager(unittest.TestCase):
    """Test prompts manager functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PromptsManager(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        self.assertIsNotNone(self.manager.config)
        self.assertIsInstance(self.manager.config.base_prompts, dict)
        self.assertIsInstance(self.manager.config.extra_prompts, dict)
    
    def test_add_base_prompt(self):
        """Test adding base prompts."""
        success = self.manager.add_base_prompt(
            "Test Prompt",
            "testing",
            "text",
            "This is a test prompt."
        )
        
        self.assertTrue(success)
        
        base_prompts = self.manager.get_base_prompts()
        self.assertEqual(len(base_prompts), 1)
        
        prompt = list(base_prompts.values())[0]
        self.assertEqual(prompt.name, "Test Prompt")
        self.assertEqual(prompt.category, "testing")
    
    def test_add_extra_prompt(self):
        """Test adding extra prompts."""
        success = self.manager.add_extra_prompt(
            "Extra Test",
            "testing",
            "boolean",
            "Add extra detail.",
            True
        )
        
        self.assertTrue(success)
        
        extra_prompts = self.manager.get_extra_prompts()
        self.assertEqual(len(extra_prompts), 1)
        
        prompt = list(extra_prompts.values())[0]
        self.assertEqual(prompt.name, "Extra Test")
        self.assertEqual(prompt.type, "boolean")
        self.assertTrue(prompt.default)
    
    def test_categories(self):
        """Test category functionality."""
        # Add prompts in different categories
        self.manager.add_base_prompt("Prompt 1", "category1", "text", "Test 1")
        self.manager.add_base_prompt("Prompt 2", "category2", "text", "Test 2")
        self.manager.add_extra_prompt("Extra 1", "category1", "boolean", "Extra 1")
        
        categories = self.manager.get_categories()
        self.assertIn("category1", categories)
        self.assertIn("category2", categories)
        
        # Test filtering by category
        cat1_base = self.manager.get_base_prompts_by_category("category1")
        self.assertEqual(len(cat1_base), 1)
        self.assertEqual(cat1_base[0].name, "Prompt 1")
        
        cat1_extra = self.manager.get_extra_prompts_by_category("category1")
        self.assertEqual(len(cat1_extra), 1)
        self.assertEqual(cat1_extra[0].name, "Extra 1")


if __name__ == '__main__':
    unittest.main()

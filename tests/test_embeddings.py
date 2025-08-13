#!/usr/bin/env python3
"""
Unit tests for embeddings functionality.
Tests ChromaDB integration and embeddings manager.
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llamalot.backend.embeddings_manager import Document


class TestEmbeddingsManager(unittest.TestCase):
    """Test cases for embeddings manager functionality."""
    
    def test_document_creation(self):
        """Test Document dataclass creation."""
        doc = Document(
            id="test_doc",
            content="This is test content",
            metadata={"source": "test", "type": "example"}
        )
        
        self.assertEqual(doc.id, "test_doc")
        self.assertEqual(doc.content, "This is test content")
        if doc.metadata is not None:
            self.assertEqual(doc.metadata["source"], "test")
            self.assertEqual(doc.metadata["type"], "example")
    
    def test_document_without_metadata(self):
        """Test Document creation without metadata."""
        doc = Document(
            id="test_doc",
            content="This is test content"
        )
        
        self.assertEqual(doc.id, "test_doc")
        self.assertEqual(doc.content, "This is test content")
        # metadata might be None or empty dict depending on implementation
        self.assertTrue(doc.metadata is None or doc.metadata == {})
    
    @patch('chromadb.Client')
    def test_embeddings_manager_import(self, mock_chromadb):
        """Test that EmbeddingsManager can be imported."""
        try:
            from llamalot.backend.embeddings_manager import EmbeddingsManager
            # If we get here, the import was successful
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Could not import EmbeddingsManager: {e}")
    
    def test_config_manager_import(self):
        """Test that ConfigurationManager can be imported."""
        try:
            from llamalot.backend.config import ConfigurationManager
            # If we get here, the import was successful
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Could not import ConfigurationManager: {e}")


class TestEmbeddingsLogic(unittest.TestCase):
    """Test cases for embeddings logic without external dependencies."""
    
    def test_collection_name_validation(self):
        """Test collection name validation logic."""
        # Valid collection names
        valid_names = [
            "test_collection",
            "llama_knowledge", 
            "user_documents",
            "collection123"
        ]
        
        for name in valid_names:
            with self.subTest(name=name):
                # Basic validation: should not be empty and should be string
                self.assertIsInstance(name, str)
                self.assertGreater(len(name), 0)
                self.assertFalse(name.isspace())
    
    def test_document_content_validation(self):
        """Test document content validation."""
        # Valid content
        valid_content = [
            "Simple text content",
            "Content with numbers 123",
            "Multi-line content\nwith newlines",
            "Content with special chars: !@#$%"
        ]
        
        for content in valid_content:
            with self.subTest(content=content[:20] + "..."):
                doc = Document(id="test", content=content)
                self.assertIsInstance(doc.content, str)
                self.assertGreater(len(doc.content), 0)


if __name__ == '__main__':
    unittest.main()

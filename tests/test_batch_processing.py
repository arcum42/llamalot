#!/usr/bin/env python3
"""
Unit tests for batch processing functionality.
Tests wildcard substitution and batch processing logic.
"""

import unittest
import tempfile
import os
from pathlib import Path

# Add src to path for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llamalot.models.chat import ChatImage


class TestBatchProcessingLogic(unittest.TestCase):
    """Test cases for batch processing logic (without GUI dependencies)."""
    
    def get_output_filename(self, image_path: str) -> str:
        """Get the output text filename for an image (mimics the method in BatchProcessingPanel)."""
        path = Path(image_path)
        return str(path.with_suffix('.txt'))

    def process_prompt_wildcards(self, prompt: str, image_path: str) -> str:
        """
        Process wildcards in the prompt, substituting them with content from existing files.
        This mimics the _process_prompt_wildcards method from BatchProcessingPanel.
        """
        processed_prompt = prompt
        
        # Handle %description% wildcard
        if '%description%' in processed_prompt:
            try:
                # Get the path to the text file for this image
                text_file_path = self.get_output_filename(image_path)
                
                if os.path.exists(text_file_path):
                    # Read existing content
                    with open(text_file_path, 'r', encoding='utf-8') as f:
                        existing_content = f.read().strip()
                else:
                    # File doesn't exist, substitute with empty string
                    existing_content = ""
                
                # Replace the wildcard
                processed_prompt = processed_prompt.replace('%description%', existing_content)
                
            except Exception:
                # On error, just replace with empty string
                processed_prompt = processed_prompt.replace('%description%', "")
        
        return processed_prompt
    
    def test_get_output_filename(self):
        """Test output filename generation."""
        test_cases = [
            ("test_image.jpg", "test_image.txt"),
            ("photo.png", "photo.txt"),
            ("/path/to/image.jpeg", "/path/to/image.txt"),
        ]
        
        for image_path, expected in test_cases:
            with self.subTest(image_path=image_path):
                result = self.get_output_filename(image_path)
                self.assertEqual(result, expected)
    
    def test_wildcard_substitution_with_existing_file(self):
        """Test %description% wildcard substitution with existing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test image path and corresponding text file
            image_path = Path(temp_dir) / "test_image.jpg"
            text_path = Path(temp_dir) / "test_image.txt"
            
            # Create the text file with existing content
            existing_content = "This is a beautiful landscape with mountains and trees."
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(existing_content)
            
            test_cases = [
                {
                    "prompt": "Describe this image: %description%",
                    "expected": f"Describe this image: {existing_content}",
                },
                {
                    "prompt": "Based on: %description% - now add more details about colors.",
                    "expected": f"Based on: {existing_content} - now add more details about colors.",
                },
                {
                    "prompt": "Multiple wildcards: %description% and %description% again",
                    "expected": f"Multiple wildcards: {existing_content} and {existing_content} again",
                },
                {
                    "prompt": "No wildcards in this prompt",
                    "expected": "No wildcards in this prompt",
                }
            ]
            
            for test_case in test_cases:
                with self.subTest(prompt=test_case["prompt"]):
                    result = self.process_prompt_wildcards(test_case["prompt"], str(image_path))
                    self.assertEqual(result, test_case["expected"])
    
    def test_wildcard_substitution_with_missing_file(self):
        """Test %description% wildcard substitution with missing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use a non-existent file path
            non_existent_path = str(Path(temp_dir) / "non_existent.jpg")
            
            prompt = "Existing description: %description% - Please describe this image."
            expected = "Existing description:  - Please describe this image."
            
            result = self.process_prompt_wildcards(prompt, non_existent_path)
            self.assertEqual(result, expected)
    
    def test_wildcard_error_handling(self):
        """Test wildcard processing error handling."""
        # Use an invalid path
        invalid_path = "/invalid/path/that/does/not/exist/test.jpg"
        
        prompt = "Test: %description% content"
        expected = "Test:  content"  # Should substitute empty string on error
        
        result = self.process_prompt_wildcards(prompt, invalid_path)
        self.assertEqual(result, expected)
    
    def test_no_wildcards(self):
        """Test prompt processing with no wildcards."""
        prompt = "This prompt has no wildcards at all."
        expected = "This prompt has no wildcards at all."
        
        result = self.process_prompt_wildcards(prompt, "/tmp/test.jpg")
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()

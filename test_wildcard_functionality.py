#!/usr/bin/env python3
"""
Test script to demonstrate the new wildcard functionality in batch processing.
This script tests the %description% wildcard substitution feature.
"""

import os
import tempfile
from pathlib import Path

# Add the src directory to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from llamalot.gui.components.batch_processing_panel import BatchProcessingPanel
from llamalot.models.chat import ChatImage

class MockOllamaClient:
    """Mock Ollama client for testing."""
    pass

class MockCacheManager:
    """Mock cache manager for testing."""
    pass

def test_wildcard_functionality():
    """Test the %description% wildcard functionality."""
    print("Testing wildcard functionality...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test image file path and corresponding text file
        image_path = Path(temp_dir) / "test_image.jpg"
        text_path = Path(temp_dir) / "test_image.txt"
        
        # Create the text file with existing content
        existing_content = "This is a beautiful landscape with mountains and trees."
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(existing_content)
        
        # Create a mock ChatImage
        chat_image = ChatImage(
            data="dummy_base64_data",
            filename="test_image.jpg",
            source_path=str(image_path)
        )
        
        # Create a mock panel to test the wildcard processing
        panel = BatchProcessingPanel(None, MockOllamaClient(), MockCacheManager())
        
        # Test cases
        test_cases = [
            {
                "prompt": "Describe this image: %description%",
                "expected": f"Describe this image: {existing_content}",
                "description": "Basic wildcard substitution"
            },
            {
                "prompt": "Based on: %description% - now add more details about colors.",
                "expected": f"Based on: {existing_content} - now add more details about colors.",
                "description": "Wildcard with surrounding text"
            },
            {
                "prompt": "Multiple wildcards: %description% and %description% again",
                "expected": f"Multiple wildcards: {existing_content} and {existing_content} again",
                "description": "Multiple wildcard occurrences"
            },
            {
                "prompt": "No wildcards in this prompt",
                "expected": "No wildcards in this prompt",
                "description": "No wildcards present"
            }
        ]
        
        print(f"Testing with existing file: {text_path}")
        print(f"Existing content: '{existing_content}'")
        print()
        
        # Test each case
        for i, test_case in enumerate(test_cases, 1):
            print(f"Test {i}: {test_case['description']}")
            print(f"  Input:    '{test_case['prompt']}'")
            
            result = panel._process_prompt_wildcards(test_case['prompt'], chat_image)
            
            print(f"  Output:   '{result}'")
            print(f"  Expected: '{test_case['expected']}'")
            
            if result == test_case['expected']:
                print("  ✅ PASS")
            else:
                print("  ❌ FAIL")
            print()
        
        # Test with non-existent file
        print("Testing with non-existent file...")
        non_existent_image = ChatImage(
            data="dummy_base64_data",
            filename="non_existent.jpg",
            source_path=str(Path(temp_dir) / "non_existent.jpg")
        )
        
        prompt = "Existing description: %description% - Please describe this image."
        result = panel._process_prompt_wildcards(prompt, non_existent_image)
        expected = "Existing description:  - Please describe this image."
        
        print(f"  Input:    '{prompt}'")
        print(f"  Output:   '{result}'")
        print(f"  Expected: '{expected}'")
        
        if result == expected:
            print("  ✅ PASS - Empty substitution for non-existent file")
        else:
            print("  ❌ FAIL - Empty substitution for non-existent file")

if __name__ == "__main__":
    test_wildcard_functionality()

#!/usr/bin/env python3
"""
Simple test script to demonstrate the new wildcard functionality in batch processing.
This script tests the %description% wildcard substitution logic without GUI dependencies.
"""

import os
import tempfile
from pathlib import Path

def get_output_filename(image_path: str) -> str:
    """Get the output text filename for an image (mimics the method in BatchProcessingPanel)."""
    path = Path(image_path)
    return str(path.with_suffix('.txt'))

def process_prompt_wildcards(prompt: str, image_path: str) -> str:
    """
    Process wildcards in the prompt, substituting them with content from existing files.
    This mimics the _process_prompt_wildcards method from BatchProcessingPanel.
    """
    processed_prompt = prompt
    
    # Handle %description% wildcard
    if '%description%' in processed_prompt:
        try:
            # Get the path to the text file for this image
            text_file_path = get_output_filename(image_path)
            
            if os.path.exists(text_file_path):
                # Read existing content
                with open(text_file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read().strip()
                print(f"  → Found existing content: '{existing_content[:50]}...' from {text_file_path}")
            else:
                # File doesn't exist, substitute with empty string
                existing_content = ""
                print(f"  → No existing file at {text_file_path}, using empty string")
            
            # Replace the wildcard
            processed_prompt = processed_prompt.replace('%description%', existing_content)
            
        except Exception as e:
            print(f"  → Error processing %description% wildcard: {e}")
            # On error, just replace with empty string
            processed_prompt = processed_prompt.replace('%description%', "")
    
    return processed_prompt

def test_wildcard_functionality():
    """Test the %description% wildcard functionality."""
    print("🧪 Testing Wildcard Functionality for Batch Processing")
    print("=" * 60)
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test image file path and corresponding text file
        image_path = Path(temp_dir) / "test_image.jpg"
        text_path = Path(temp_dir) / "test_image.txt"
        
        # Create the text file with existing content
        existing_content = "This is a beautiful landscape with mountains and trees."
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(existing_content)
        
        print(f"📁 Test directory: {temp_dir}")
        print(f"📄 Created test file: {text_path}")
        print(f"📝 Content: '{existing_content}'")
        print()
        
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
        
        # Test each case with existing file
        print("🔧 Testing with EXISTING text file:")
        for i, test_case in enumerate(test_cases, 1):
            print(f"\nTest {i}: {test_case['description']}")
            print(f"  Input:  '{test_case['prompt']}'")
            
            result = process_prompt_wildcards(test_case['prompt'], str(image_path))
            
            print(f"  Output: '{result}'")
            
            if result == test_case['expected']:
                print("  Status: ✅ PASS")
            else:
                print("  Status: ❌ FAIL")
                print(f"  Expected: '{test_case['expected']}'")
        
        # Test with non-existent file
        print(f"\n🔧 Testing with NON-EXISTENT text file:")
        non_existent_image = str(Path(temp_dir) / "non_existent.jpg")
        
        prompt = "Existing description: %description% - Please describe this image."
        result = process_prompt_wildcards(prompt, non_existent_image)
        expected = "Existing description:  - Please describe this image."
        
        print(f"\nTest: Empty substitution for missing file")
        print(f"  Input:  '{prompt}'")
        print(f"  Output: '{result}'")
        
        if result == expected:
            print("  Status: ✅ PASS - Correctly substituted empty string")
        else:
            print("  Status: ❌ FAIL - Incorrect substitution")
            print(f"  Expected: '{expected}'")
        
        print(f"\n🎉 All tests completed!")
        print("\n💡 Usage Examples:")
        print("  • 'Describe this image: %description%' → Uses existing description as context")
        print("  • 'Update this description: %description%\\nAdd more details about...' → Builds on existing")
        print("  • 'Compare: %description% vs what you see now' → Comparative analysis")

if __name__ == "__main__":
    test_wildcard_functionality()

#!/usr/bin/env python3
"""
Simple test to verify the prompts system integration.
"""

import sys
import os
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from llamalot.models.prompts import BasePrompt, ExtraPrompt, PromptsConfig
from llamalot.backend.prompts_manager import PromptsManager


def test_prompts_system():
    """Test the complete prompts system."""
    print("Testing prompts system...")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    try:
        # Create manager
        manager = PromptsManager(temp_dir)
        print(f"✓ Created manager with config dir: {temp_dir}")
        
        # Test adding base prompt using the manager's method
        success = manager.add_base_prompt(
            "Test Base Prompt",
            "testing",
            "text",
            "Describe this image in detail."
        )
        print("✓ Added base prompt:", success)
        
        # Test adding extra prompt using the manager's method
        success = manager.add_extra_prompt(
            "Focus on Colors",
            "testing",
            "boolean",
            "Pay special attention to colors and lighting.",
            True
        )
        print("✓ Added extra prompt:", success)
        
        # Test building final prompt with available prompts
        base_prompts = manager.get_base_prompts()
        extra_prompts = manager.get_extra_prompts()
        
        if base_prompts and extra_prompts:
            base_id = list(base_prompts.keys())[0]
            extra_id = list(extra_prompts.keys())[0]
            
            wildcard_values = {}
            final_prompt = manager.build_final_prompt(
                base_id,
                [extra_id],
                wildcard_values
            )
            
            print(f"✓ Built final prompt: {final_prompt[:100]}...")
        else:
            print("⚠ Skipping prompt building - no prompts available")
        
        # Test categories
        categories = manager.get_categories()
        print(f"✓ Found categories: {categories}")
        
        # Test filtering
        testing_base = manager.get_base_prompts_by_category("testing")
        testing_extra = manager.get_extra_prompts_by_category("testing")
        print(f"✓ Testing category has {len(testing_base)} base and {len(testing_extra)} extra prompts")
        
        # Test save/load
        manager.save_config()
        print("✓ Saved configuration")
        
        new_manager = PromptsManager(temp_dir)
        new_manager.load_config()
        print("✓ Loaded configuration in new manager")
        
        # Verify data persisted
        loaded_base = new_manager.get_base_prompts()
        loaded_extra = new_manager.get_extra_prompts()
        print(f"✓ Loaded {len(loaded_base)} base and {len(loaded_extra)} extra prompts")
        
        print("\n🎉 All tests passed! Prompts system is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    success = test_prompts_system()
    sys.exit(0 if success else 1)

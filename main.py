#!/usr/bin/env python3
"""
Main entry point for LlamaLot application.

This script initializes and starts the wxPython GUI application.
"""

import sys
import os

# Add the src directory to the Python path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from llamalot.main import main

if __name__ == "__main__":
    main()
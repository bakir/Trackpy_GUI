#!/usr/bin/env python3
"""
Main entry point for the Particle Tracking GUI application with project management.

This file serves as the entry point and imports the main application from the src package.
"""

import sys
import os

# Add the current directory to Python path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main_with_projects import main

if __name__ == "__main__":
    main()
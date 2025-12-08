#!/usr/bin/env python3
"""
Main entry point for the Particle Tracking GUI application with project management.

Description: This file serves as the entry point and imports the main application from the src package.

Copyright (c) 2025, Jacqueline Reynaga, Kevin Pillsbury, Bakir Husremovic
License: BSD 3-Clause License
Date: 2025-12-08
"""

import sys
import os

# Add the current directory to Python path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    main()

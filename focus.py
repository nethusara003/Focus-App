#!/usr/bin/env python3
import sys
import os

# Ensure the current directory is in python's search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from daily_focus.focus import main

if __name__ == "__main__":
    main()

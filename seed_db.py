#!/usr/bin/env python3
"""
Database Seeder CLI

Simple command-line interface to run database seeders.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run seeder
from seeds.seed import run_seeds

if __name__ == "__main__":
    # Check if virtual environment is activated
    if not os.environ.get('VIRTUAL_ENV') and not sys.prefix != sys.base_prefix:
        print("⚠️  Warning: Virtual environment may not be activated")
    
    # Run the seeders
    results = run_seeds()
    
    # Exit with appropriate code
    exit_code = 0 if results["success"] else 1
    sys.exit(exit_code)
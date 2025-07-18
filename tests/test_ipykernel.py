#!/usr/bin/env python3
"""
Test script to verify ipykernel installation
"""

import sys
import subprocess

def test_ipykernel():
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    
    try:
        import ipykernel
        print(f"✓ ipykernel imported successfully from: {ipykernel.__file__}")
    except ImportError as e:
        print(f"✗ Failed to import ipykernel: {e}")
        return False
    
    try:
        # Test if we can start a kernel
        result = subprocess.run([
            sys.executable, '-m', 'ipykernel', '--version'
        ], capture_output=True, text=True, timeout=10)
        print(f"✓ ipykernel version: {result.stdout.strip()}")
    except Exception as e:
        print(f"✗ Failed to run ipykernel: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_ipykernel()
    sys.exit(0 if success else 1) 
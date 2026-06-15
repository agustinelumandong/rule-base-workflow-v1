#!/usr/bin/env python3
import unittest
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if __name__ == "__main__":
    print("Discovering tests...")
    loader = unittest.defaultTestLoader
    suite = loader.discover("tests")
    
    with open("scratch_results.log", "w", encoding="utf-8") as f:
        f.write("Running discovered tests...\n")
        runner = unittest.TextTestRunner(verbosity=2, stream=f)
        result = runner.run(suite)
        f.write(f"\nSuccessful: {result.wasSuccessful()}\n")
        f.write(f"Errors: {len(result.errors)}\n")
        f.write(f"Failures: {len(result.failures)}\n")
    
    sys.exit(0)

#!/usr/bin/env python
"""
TDD Phase Verification Script

This script helps verify the different phases of Test-Driven Development:
1. Red phase: Tests fail because implementation doesn't exist
2. Green phase: Tests pass after implementing the code
3. Refactor phase: Tests pass after code improvements

Usage:
    python run_tdd_verification.py --phase red
    python run_tdd_verification.py --phase green
    python run_tdd_verification.py --phase refactor
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_tests(test_path=None):
    """
    Run the pytest command for the specified test path
    
    Args:
        test_path: Specific test file or directory to run tests for
        
    Returns:
        tuple: (return_code, stdout, stderr)
    """
    cmd = ["pytest", "-v"]
    if test_path:
        cmd.append(str(test_path))
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr


def verify_red_phase():
    """
    Verify the 'red' phase of TDD - tests should fail
    because implementation doesn't exist yet
    """
    print("=== Verifying RED phase ===")
    print("Tests should fail since implementation doesn't exist yet.")
    
    return_code, stdout, stderr = run_tests()
    
    if return_code != 0:
        print("✅ RED phase verified: Tests are failing as expected.")
        print("\nTest output:")
        print(stdout)
    else:
        print("❌ ERROR: Tests are passing, but they should fail in the RED phase.")
        print("Make sure implementation does not exist yet.")
    
    return return_code != 0


def verify_green_phase():
    """
    Verify the 'green' phase of TDD - tests should pass
    after minimal implementation
    """
    print("=== Verifying GREEN phase ===")
    print("Tests should pass with the minimal implementation.")
    
    return_code, stdout, stderr = run_tests()
    
    if return_code == 0:
        print("✅ GREEN phase verified: Tests are passing as expected.")
        print("\nTest output:")
        print(stdout)
    else:
        print("❌ ERROR: Tests are failing, but they should pass in the GREEN phase.")
        print("Implementation is incomplete or incorrect.")
        print("\nTest output:")
        print(stdout)
    
    return return_code == 0


def verify_refactor_phase():
    """
    Verify the 'refactor' phase of TDD - tests should still pass
    after refactoring the code
    """
    print("=== Verifying REFACTOR phase ===")
    print("Tests should pass after code refactoring.")
    
    return_code, stdout, stderr = run_tests()
    
    if return_code == 0:
        print("✅ REFACTOR phase verified: Tests are passing after refactoring.")
        print("\nTest output:")
        print(stdout)
    else:
        print("❌ ERROR: Tests are failing after refactoring.")
        print("Refactoring introduced regressions.")
        print("\nTest output:")
        print(stdout)
    
    return return_code == 0


def main():
    parser = argparse.ArgumentParser(description="Verify TDD phases")
    parser.add_argument(
        "--phase", 
        choices=["red", "green", "refactor"],
        required=True,
        help="TDD phase to verify"
    )
    parser.add_argument(
        "--test-path",
        help="Specific test file or directory to run"
    )
    
    args = parser.parse_args()
    
    if args.phase == "red":
        success = verify_red_phase()
    elif args.phase == "green":
        success = verify_green_phase()
    elif args.phase == "refactor":
        success = verify_refactor_phase()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()

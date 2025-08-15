#!/usr/bin/env python3
"""Test runner for Raycast Focus Tracker tests."""

import sys
import subprocess
import argparse
from pathlib import Path

def run_tests(test_type="all", verbose=True, coverage=False):
    """Run tests based on the specified type.
    
    Args:
        test_type (str): Type of tests to run ("unit", "integration", "e2e", "all")
        verbose (bool): Whether to run in verbose mode
        coverage (bool): Whether to run with coverage reporting
    """
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add coverage if requested
    if coverage:
        cmd.extend(["--cov=raycast_focus_tracker", "--cov-report=term-missing", "--cov-report=html"])
    
    # Determine which tests to run
    if test_type == "unit":
        cmd.append("tests/unit/")
    elif test_type == "integration":
        cmd.append("tests/integration/")
    elif test_type == "e2e":
        cmd.append("tests/e2e/")
    elif test_type == "all":
        cmd.append("tests/")
    else:
        print(f"Unknown test type: {test_type}")
        return 1
    
    # Run the tests
    print(f"Running {test_type} tests...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Run Raycast Focus Tracker tests")
    parser.add_argument(
        "type", 
        nargs="?", 
        default="all",
        choices=["unit", "integration", "e2e", "all"],
        help="Type of tests to run (default: all)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Run tests in quiet mode"
    )
    parser.add_argument(
        "-c", "--coverage",
        action="store_true", 
        help="Run tests with coverage reporting"
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies before running"
    )
    
    args = parser.parse_args()
    
    # Install dependencies if requested
    if args.install_deps:
        print("Installing test dependencies...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-cov"], check=True)
            print("Dependencies installed successfully")
        except subprocess.CalledProcessError:
            print("Failed to install dependencies")
            return 1
    
    # Run tests
    return run_tests(
        test_type=args.type,
        verbose=not args.quiet,
        coverage=args.coverage
    )

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Test runner script for find-a-workinator.
Provides easy commands to run different types of tests.
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and print results."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def main():
    """Main test runner function."""
    if len(sys.argv) < 2:
        print("Usage: python test_runner.py <command>")
        print("\nAvailable commands:")
        print("  all        - Run all tests")
        print("  unit       - Run only unit tests")
        print("  integration - Run only integration tests")
        print("  utils      - Run utility function tests")
        print("  db         - Run database tests")
        print("  scraping   - Run scraping tests")
        print("  logger     - Run logger tests")
        print("  coverage   - Run tests with coverage report")
        print("  install    - Install test dependencies")
        return
    
    command = sys.argv[1].lower()
    
    # Check if pytest is available
    try:
        subprocess.run(['pytest', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ pytest not found. Run 'python test_runner.py install' first.")
        return
    
    success = True
    
    if command == 'install':
        success = run_command(['pip', 'install', '-r', 'requirements.txt'], 
                            "Installing test dependencies")
    
    elif command == 'all':
        success = run_command(['pytest', 'tests/', '-v'], 
                            "All tests")
    
    elif command == 'unit':
        success = run_command(['pytest', 'tests/', '-v', '-m', 'unit'], 
                            "Unit tests")
    
    elif command == 'integration':
        success = run_command(['pytest', 'tests/', '-v', '-m', 'integration'], 
                            "Integration tests")
    
    elif command == 'utils':
        success = run_command(['pytest', 'tests/test_utils.py', '-v'], 
                            "Utility function tests")
    
    elif command == 'db':
        success = run_command(['pytest', 'tests/test_db_manager.py', '-v'], 
                            "Database tests")
    
    elif command == 'scraping':
        success = run_command(['pytest', 'tests/test_scraping.py', '-v'], 
                            "Scraping tests")
    
    elif command == 'logger':
        success = run_command(['pytest', 'tests/test_logger.py', '-v'], 
                            "Logger tests")
    
    elif command == 'coverage':
        # Try to install coverage if not available
        try:
            subprocess.run(['coverage', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Installing coverage...")
            subprocess.run(['pip', 'install', 'coverage'], check=True)
        
        success = run_command(['coverage', 'run', '-m', 'pytest', 'tests/', '-v'], 
                            "Tests with coverage")
        if success:
            run_command(['coverage', 'report'], "Coverage report")
            run_command(['coverage', 'html'], "HTML coverage report")
            print("\n📊 HTML coverage report generated in htmlcov/index.html")
    
    else:
        print(f"❌ Unknown command: {command}")
        return
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 All operations completed successfully!")
    else:
        print("💥 Some operations failed. Check the output above.")
    print('='*60)

if __name__ == '__main__':
    main()
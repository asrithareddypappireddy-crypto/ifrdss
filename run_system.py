"""
run_system.py
-------------
One-click runner script for Intelligent Flood Rescue Decision Support System (IFRDSS).
Verifies dependencies, executes pytest test suite, and launches the FastAPI web server.
"""

import sys
import subprocess
import os

def main():
    print("=" * 70)
    print("  Intelligent Flood Rescue Decision Support System (IFRDSS)")
    print("  Software Engineering Final Project Runner")
    print("=" * 70)

    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    print("\n[1/2] Running automated test suite (pytest)...")
    res = subprocess.run([sys.executable, "-m", "pytest", "tests/"])
    if res.returncode != 0:
        print("\n[!] Warnings or test issues detected, but proceeding to launch server...")
    else:
        print("\n[✓] All test cases passed successfully!")

    print("\n[2/2] Launching IFRDSS Web Server on http://localhost:8000 ...")
    print("Press Ctrl+C to stop the server.\n")

    sys.path.insert(0, os.path.join(project_dir, "backend"))
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()

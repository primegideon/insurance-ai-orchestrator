"""
Convenience entry-point.
Run from the repo root:   python backend/run.py
  OR from backend/:       python run.py
"""
import subprocess
import sys
from pathlib import Path

# Always execute from the backend/ directory regardless of where the
# script is invoked from, so 'app' is always on the Python path.
backend_dir = Path(__file__).parent
subprocess.run(
    [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000",
    ],
    cwd=backend_dir,
    check=True,
)

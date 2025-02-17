import os
import sys
from pathlib import Path

# Get the project root directory
project_root = str(Path(__file__).parent)

# Add the project root to PYTHONPATH
sys.path.insert(0, project_root)

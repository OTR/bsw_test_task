import sys
from pathlib import Path

# Get the project root directory
project_root = str(Path(__file__).parent)

# Add the project root to PYTHONPATH
sys.path.insert(0, project_root)

"""
# Uncomment in case of more gradular pytest configuration
# For now pytest settings are located in pyproject.toml
import pytest

# Configure pytest-asyncio
def pytest_configure(config):
    config.option.asyncio_mode = "strict"

# Set default fixture loop scope
pytest_plugins = ["pytest_asyncio.plugin"]
pytest_asyncio_default_fixture_loop_scope = "function"
"""
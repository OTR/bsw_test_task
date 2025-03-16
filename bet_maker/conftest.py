import sys
from pathlib import Path

project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)

"""
import pytest

def pytest_configure(config):
    config.option.asyncio_mode = "strict"

pytest_plugins = ["pytest_asyncio.plugin"]
pytest_asyncio_default_fixture_loop_scope = "function"
"""

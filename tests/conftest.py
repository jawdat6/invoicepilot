import pytest
from pathlib import Path

@pytest.fixture
def tmp_out(tmp_path):
    """Temporary output directory for downloaded files."""
    out = tmp_path / "Invoices"
    out.mkdir()
    return out

@pytest.fixture
def minimal_config():
    """Minimal valid config dict for testing."""
    return {
        "output_dir": "~/Downloads/Invoices",
        "connectors": {}
    }

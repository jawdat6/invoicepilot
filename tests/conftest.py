import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


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

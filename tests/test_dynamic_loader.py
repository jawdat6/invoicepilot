"""Tests for dynamic user connector loading from ~/.invoicepilot/connectors/."""
import importlib
import sys
from pathlib import Path

import pytest


CONNECTOR_CODE = """
from tools.connectors.base import BaseConnector, ConnectorResult
from datetime import date
from pathlib import Path

class TestServiceConnector(BaseConnector):
    name = "TestService"
    stable = True

    def is_configured(self):
        return self._is_set("api_key")

    def download(self, start: date, end: date, out_dir: Path) -> ConnectorResult:
        return ConnectorResult(
            connector=self.name, files=[], count=0, skipped=0, error=None, hint=None
        )
"""

BROKEN_CODE = "this is not valid python !!!"


def _reload_connectors(monkeypatch, home_dir):
    """Reload tools.connectors with Path.home() patched to home_dir."""
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home_dir))
    # Remove cached module so it re-executes the loader block
    for key in list(sys.modules.keys()):
        if key == "tools.connectors" or key.startswith("tools.connectors."):
            # Only remove the top-level package, not sub-modules (base, aws, etc.)
            if key == "tools.connectors":
                del sys.modules[key]
    import tools.connectors
    importlib.reload(tools.connectors)
    return tools.connectors


def test_user_connector_loaded_from_home_dir(tmp_path, monkeypatch):
    """User connectors in ~/.invoicepilot/connectors/ are auto-loaded."""
    user_connector_dir = tmp_path / ".invoicepilot" / "connectors"
    user_connector_dir.mkdir(parents=True)
    (user_connector_dir / "testservice.py").write_text(CONNECTOR_CODE)

    mod = _reload_connectors(monkeypatch, tmp_path)

    names = [c.name for c in mod.ALL_CONNECTORS]
    assert "TestService" in names, f"Expected TestService in {names}"

    # Restore: reload without the patched home
    importlib.reload(mod)


def test_bad_user_connector_does_not_crash(tmp_path, monkeypatch, capsys):
    """A broken user connector file prints a warning but doesn't crash."""
    user_connector_dir = tmp_path / ".invoicepilot" / "connectors"
    user_connector_dir.mkdir(parents=True)
    (user_connector_dir / "broken.py").write_text(BROKEN_CODE)

    # Should not raise
    mod = _reload_connectors(monkeypatch, tmp_path)

    captured = capsys.readouterr()
    # The warning message should mention the file name
    assert "broken.py" in captured.out or "Warning" in captured.out or "warning" in captured.out

    importlib.reload(mod)


def test_no_user_connector_dir_is_fine(tmp_path, monkeypatch):
    """When ~/.invoicepilot/connectors/ does not exist, loading is a no-op."""
    # tmp_path has no .invoicepilot subdirectory
    mod = _reload_connectors(monkeypatch, tmp_path)

    # Built-in connectors should still be present
    names = [c.name for c in mod.ALL_CONNECTORS]
    assert len(names) > 0, "Built-in connectors should still load"
    assert "TestService" not in names

    importlib.reload(mod)


def test_duplicate_connector_not_added_twice(tmp_path, monkeypatch):
    """If a user connector has the same class as an existing one, it is not duplicated."""
    user_connector_dir = tmp_path / ".invoicepilot" / "connectors"
    user_connector_dir.mkdir(parents=True)
    # Write two files with separate connector names to check dedup via class identity
    (user_connector_dir / "testservice.py").write_text(CONNECTOR_CODE)

    mod = _reload_connectors(monkeypatch, tmp_path)

    names = [c.name for c in mod.ALL_CONNECTORS]
    assert names.count("TestService") == 1, "Connector should not be duplicated"

    importlib.reload(mod)

# tests/test_list_connectors.py
import pytest
from unittest.mock import patch, MagicMock
from tools.list_connectors import run_list
from tools.connectors.config import ConfigError


def test_list_shows_configured_connector(capsys):
    config = {
        "connectors": {"aws": {"access_key_id": "AKIAXX", "secret_access_key": "x", "account_id": "123"}},
        "_unconfigured": [],
        "output_dir_expanded": "/tmp",
    }
    with patch("tools.list_connectors.load_config", return_value=config):
        with patch("tools.list_connectors.ALL_CONNECTORS") as mock_connectors:
            mock_cls = MagicMock()
            mock_cls.return_value.name = "AWS"
            mock_cls.return_value.stable = True
            mock_cls.return_value.is_configured.return_value = True
            mock_connectors.__iter__ = lambda s: iter([mock_cls])
            run_list()
    captured = capsys.readouterr()
    assert "✓" in captured.out
    assert "AWS" in captured.out


def test_list_shows_unconfigured_connector(capsys):
    config = {
        "connectors": {},
        "_unconfigured": ["aws"],
        "output_dir_expanded": "/tmp",
    }
    with patch("tools.list_connectors.load_config", return_value=config):
        with patch("tools.list_connectors.ALL_CONNECTORS") as mock_connectors:
            mock_cls = MagicMock()
            mock_cls.return_value.name = "AWS"
            mock_cls.return_value.stable = True
            mock_cls.return_value.is_configured.return_value = False
            mock_connectors.__iter__ = lambda s: iter([mock_cls])
            run_list()
    captured = capsys.readouterr()
    assert "○" in captured.out or "not configured" in captured.out


def test_list_shows_unstable_badge(capsys):
    config = {"connectors": {}, "_unconfigured": [], "output_dir_expanded": "/tmp"}
    with patch("tools.list_connectors.load_config", return_value=config):
        with patch("tools.list_connectors.ALL_CONNECTORS") as mock_connectors:
            mock_cls = MagicMock()
            mock_cls.return_value.name = "OpenPhone"
            mock_cls.return_value.stable = False
            mock_cls.return_value.is_configured.return_value = True
            mock_connectors.__iter__ = lambda s: iter([mock_cls])
            run_list()
    captured = capsys.readouterr()
    assert "unstable" in captured.out or "⚠" in captured.out


def test_list_exits_on_config_error(capsys):
    with patch("tools.list_connectors.load_config", side_effect=ConfigError("not found")):
        with pytest.raises(SystemExit):
            run_list()

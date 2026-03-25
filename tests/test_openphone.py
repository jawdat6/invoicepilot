# tests/test_openphone.py
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from tools.connectors.openphone import OpenPhoneConnector


@pytest.fixture
def op_config():
    return {"email": "user@example.com", "password": "mypass"}


def test_openphone_is_unstable(op_config):
    assert OpenPhoneConnector(config=op_config).stable is False


def test_openphone_is_configured(op_config):
    assert OpenPhoneConnector(config=op_config).is_configured() is True


def test_openphone_not_configured():
    assert OpenPhoneConnector(config={}).is_configured() is False


@patch("tools.connectors.openphone.sync_playwright")
def test_openphone_returns_error_when_playwright_unavailable(mock_pw, tmp_out, op_config):
    mock_pw.side_effect = ImportError("playwright not installed")
    c = OpenPhoneConnector(config=op_config)
    result = c.download(date(2025, 3, 1), date(2025, 3, 31), tmp_out)
    assert result.error is not None
    assert "playwright" in result.hint.lower()

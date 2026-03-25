# tests/test_godaddy.py
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from tools.connectors.godaddy import GoDaddyConnector


@pytest.fixture
def gd_config():
    return {"api_key": "mykey", "api_secret": "mysecret"}


def test_godaddy_is_configured(gd_config):
    assert GoDaddyConnector(config=gd_config).is_configured() is True

def test_godaddy_not_configured_when_missing():
    assert GoDaddyConnector(config={}).is_configured() is False

@patch("tools.connectors.godaddy.requests.get")
def test_godaddy_saves_orders(mock_get, tmp_out, gd_config):
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {"orders": [{"orderId": "123", "createdAt": "2025-03-15T00:00:00Z"}]},
    )
    c = GoDaddyConnector(config=gd_config)
    result = c.download(date(2025, 3, 1), date(2025, 3, 31), tmp_out)
    assert result.error is None

@patch("tools.connectors.godaddy.requests.get")
def test_godaddy_returns_error_on_auth_failure(mock_get, tmp_out, gd_config):
    mock_get.return_value = MagicMock(status_code=403, json=lambda: {"code": "UNABLE_TO_AUTHENTICATE"})
    c = GoDaddyConnector(config=gd_config)
    result = c.download(date(2025, 3, 1), date(2025, 3, 31), tmp_out)
    assert result.error is not None
    assert "production" in result.hint.lower()

# tests/test_zoho.py
import json
import pytest
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from tools.connectors.zoho import ZohoConnector


@pytest.fixture
def zoho_config(tmp_path):
    config_path = tmp_path / "config.yml"
    config_path.write_text("connectors:\n  zoho:\n    refresh_token: old_token\n")
    return {
        "client_id": "1000.xxxx",
        "client_secret": "mysecret",
        "refresh_token": "old_token",
        "org_ids": {"default": "849347283"},
        "_config_path": config_path,
    }


@patch("tools.connectors.zoho.requests.post")
@patch("tools.connectors.zoho.requests.get")
def test_zoho_downloads_invoice(mock_get, mock_post, tmp_out, zoho_config):
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"access_token": "newtoken", "refresh_token": "new_refresh"}
    )
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "invoices": [
                {"invoice_id": "inv1", "date": "2025-03-15", "invoice_number": "INV-001", "total": 100.0}
            ],
            "page_context": {"has_more_page": False}
        },
        content=b"%PDF-fake-content",
    )

    c = ZohoConnector(config=zoho_config)
    result = c.download(date(2025, 3, 1), date(2025, 3, 31), tmp_out)
    assert result.error is None
    assert result.count >= 1


@patch("tools.connectors.zoho.requests.post")
def test_zoho_updates_refresh_token_in_config(mock_post, tmp_out, zoho_config):
    """After successful token refresh, new refresh_token written to config file."""
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"access_token": "newtoken", "refresh_token": "brand_new_token"}
    )
    with patch("tools.connectors.zoho.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"invoices": [], "page_context": {"has_more_page": False}},
            content=b"",
        )
        c = ZohoConnector(config=zoho_config)
        c.download(date(2025, 3, 1), date(2025, 3, 31), tmp_out)

    config_text = zoho_config["_config_path"].read_text()
    assert "brand_new_token" in config_text


@patch("tools.connectors.zoho.requests.post")
def test_zoho_returns_error_on_auth_failure(mock_post, tmp_out, zoho_config):
    mock_post.return_value = MagicMock(
        status_code=400,
        json=lambda: {"error": "invalid_client"}
    )
    c = ZohoConnector(config=zoho_config)
    result = c.download(date(2025, 3, 1), date(2025, 3, 31), tmp_out)
    assert result.error is not None
    assert "refresh_token" in result.hint.lower()

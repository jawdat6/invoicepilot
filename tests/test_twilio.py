# tests/test_twilio.py
import json
import pytest
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock
from tools.connectors.twilio import TwilioConnector


@pytest.fixture
def twilio_config():
    return {"account_sid": "ACxxxxxxxx", "auth_token": "mytoken"}


def test_twilio_is_configured(twilio_config):
    assert TwilioConnector(config=twilio_config).is_configured() is True


def test_twilio_not_configured_when_missing():
    assert TwilioConnector(config={}).is_configured() is False


@patch("tools.connectors.twilio.requests.get")
def test_twilio_download_saves_json(mock_get, tmp_out, twilio_config):
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {"usage_records": [{"category": "sms", "price": "1.50"}]},
    )
    c = TwilioConnector(config=twilio_config)
    result = c.download(date(2025, 3, 1), date(2025, 3, 31), tmp_out)
    assert result.error is None
    assert result.count == 1


@patch("tools.connectors.twilio.requests.get")
def test_twilio_download_skips_existing(mock_get, tmp_out, twilio_config):
    (tmp_out / "Twilio_2025-03.json").write_text("{}")
    c = TwilioConnector(config=twilio_config)
    result = c.download(date(2025, 3, 1), date(2025, 3, 31), tmp_out)
    assert result.skipped == 1
    mock_get.assert_not_called()


@patch("tools.connectors.twilio.requests.get")
def test_twilio_returns_error_on_401(mock_get, tmp_out, twilio_config):
    mock_get.return_value = MagicMock(status_code=401, text="Unauthorized")
    c = TwilioConnector(config=twilio_config)
    result = c.download(date(2025, 3, 1), date(2025, 3, 31), tmp_out)
    assert result.error is not None
    assert "auth_token" in result.hint.lower()

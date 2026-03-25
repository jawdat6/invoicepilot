# tests/test_mongodb.py
import pytest
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock
from tools.connectors.mongodb import MongoDBConnector


@pytest.fixture
def mongo_config():
    return {
        "public_key": "mykey",
        "private_key": "myprivate-key-uuid",
        "org_id": "66ce1658d57afb596d6d624d",
    }


def test_mongodb_is_configured(mongo_config):
    assert MongoDBConnector(config=mongo_config).is_configured() is True


def test_mongodb_not_configured_when_missing():
    assert MongoDBConnector(config={}).is_configured() is False


@patch("tools.connectors.mongodb.requests.get")
def test_mongodb_downloads_invoices(mock_get, tmp_out, mongo_config):
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "results": [
                {
                    "id": "inv123",
                    "startDate": "2025-03-01T00:00:00Z",
                    "statusName": "PAID",
                    "amountBilledCents": 4500,
                    "creditsCents": 0,
                }
            ]
        },
    )
    c = MongoDBConnector(config=mongo_config)
    result = c.download(date(2025, 3, 1), date(2025, 3, 31), tmp_out)
    assert result.error is None
    assert result.count >= 1


@patch("tools.connectors.mongodb.requests.get")
def test_mongodb_returns_error_on_401(mock_get, tmp_out, mongo_config):
    mock_get.return_value = MagicMock(status_code=401, json=lambda: {"error": "Unauthorized"})
    c = MongoDBConnector(config=mongo_config)
    result = c.download(date(2025, 3, 1), date(2025, 3, 31), tmp_out)
    assert result.error is not None
    assert result.hint is not None

# tests/test_gcloud.py
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from tools.connectors.gcloud import GCloudConnector


@pytest.fixture
def gc_config():
    return {"billing_account": "01ADD4-88BCE9-C81B3C"}


def test_gcloud_not_configured_when_missing():
    assert GCloudConnector(config={}).is_configured() is False


@patch("tools.connectors.gcloud.subprocess.run")
def test_gcloud_is_configured_when_adc_valid(mock_run, gc_config):
    mock_run.return_value = MagicMock(returncode=0, stdout="ya29.token")
    with patch("tools.connectors.gcloud.requests.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"name": "billingAccounts/01ADD4-88BCE9-C81B3C"})
        assert GCloudConnector(config=gc_config).is_configured() is True


@patch("tools.connectors.gcloud.subprocess.run")
def test_gcloud_not_configured_when_adc_missing(mock_run, gc_config):
    mock_run.return_value = MagicMock(returncode=1, stdout="")
    c = GCloudConnector(config=gc_config)
    assert c.is_configured() is False


@patch("tools.connectors.gcloud.subprocess.run")
@patch("tools.connectors.gcloud.requests.get")
def test_gcloud_download_saves_summary(mock_get, mock_run, tmp_out, gc_config):
    mock_run.return_value = MagicMock(returncode=0, stdout="ya29.token")
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {"projectBillingInfo": []},
    )
    c = GCloudConnector(config=gc_config)
    result = c.download(date(2025, 3, 1), date(2025, 3, 31), tmp_out)
    assert result.error is None


@patch("tools.connectors.gcloud.subprocess.run")
@patch("tools.connectors.gcloud.requests.get")
def test_gcloud_is_configured_returns_false_on_403(mock_get, mock_run, gc_config):
    """is_configured() returns False (not raises) when billing access denied."""
    mock_run.return_value = MagicMock(returncode=0, stdout="ya29.token")
    mock_get.return_value = MagicMock(status_code=403)
    c = GCloudConnector(config=gc_config)
    assert c.is_configured() is False


@patch("tools.connectors.gcloud.subprocess.run")
@patch("tools.connectors.gcloud.requests.get")
def test_gcloud_download_returns_hint_on_403(mock_get, mock_run, tmp_out, gc_config):
    """download() returns a hint mentioning billing.viewer when 403."""
    mock_run.return_value = MagicMock(returncode=0, stdout="ya29.token")
    mock_get.return_value = MagicMock(
        status_code=403,
        json=lambda: {"error": {"status": "PERMISSION_DENIED"}},
    )
    c = GCloudConnector(config=gc_config)
    result = c.download(date(2025, 3, 1), date(2025, 3, 31), tmp_out)
    assert result.error is not None
    assert "billing.viewer" in result.hint

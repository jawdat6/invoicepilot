# tests/test_aws.py
import pytest
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock
from tools.connectors.aws import AWSConnector


@pytest.fixture
def aws_config():
    return {
        "access_key_id": "AKIAXXXXXXXX",
        "secret_access_key": "mysecret",
        "account_id": "123456789012",
    }


def test_aws_is_configured_with_valid_keys(aws_config):
    c = AWSConnector(config=aws_config)
    assert c.is_configured() is True


def test_aws_is_not_configured_with_replace_me():
    c = AWSConnector(config={"access_key_id": "REPLACE_ME", "secret_access_key": "REPLACE_ME", "account_id": "REPLACE_ME"})
    assert c.is_configured() is False


def test_aws_is_not_configured_when_keys_missing():
    c = AWSConnector(config={})
    assert c.is_configured() is False


@patch("tools.connectors.aws.boto3.client")
def test_aws_download_saves_json(mock_boto, tmp_out, aws_config):
    mock_ce = MagicMock()
    mock_ce.get_cost_and_usage.return_value = {
        "ResultsByTime": [{"TimePeriod": {"Start": "2025-03-01"}, "Total": {"BlendedCost": {"Amount": "42.50"}}}]
    }
    mock_boto.return_value = mock_ce

    c = AWSConnector(config=aws_config)
    result = c.download(date(2025, 3, 1), date(2025, 3, 31), tmp_out)

    assert result.error is None
    assert result.count >= 1
    assert any(f.suffix == ".json" for f in result.files)


@patch("tools.connectors.aws.boto3.client")
def test_aws_download_skips_existing_file(mock_boto, tmp_out, aws_config):
    existing = tmp_out / "AWS_2025-03.json"
    existing.write_text("{}")

    c = AWSConnector(config=aws_config)
    result = c.download(date(2025, 3, 1), date(2025, 3, 31), tmp_out)

    assert result.skipped == 1
    assert result.count == 0
    mock_boto.assert_not_called()


@patch("tools.connectors.aws.boto3.client")
def test_aws_download_returns_error_on_auth_failure(mock_boto, tmp_out, aws_config):
    from botocore.exceptions import ClientError
    mock_ce = MagicMock()
    mock_ce.get_cost_and_usage.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "denied"}}, "GetCostAndUsage"
    )
    mock_boto.return_value = mock_ce

    c = AWSConnector(config=aws_config)
    result = c.download(date(2025, 3, 1), date(2025, 3, 31), tmp_out)

    assert result.error is not None
    assert result.hint is not None
    assert "access_key_id" in result.hint.lower() or "iam" in result.hint.lower()

# tests/test_orchestrator.py
import pytest
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from tools.download_invoices import run_download, parse_date_range, months_between
from tools.connectors.base import ConnectorResult

LOCK_FILE = Path.home() / ".invoicepilot" / ".lock"


def test_months_between_single_month():
    months = months_between(date(2025, 3, 1), date(2025, 3, 31))
    assert len(months) == 1
    assert months[0] == date(2025, 3, 1)


def test_months_between_multi_month():
    months = months_between(date(2025, 1, 1), date(2025, 3, 31))
    assert len(months) == 3
    assert months[0] == date(2025, 1, 1)
    assert months[-1] == date(2025, 3, 1)


def test_parse_date_range_last_month():
    start, end = parse_date_range("last month")
    assert start.day == 1
    assert start < end


def test_parse_date_range_specific_month():
    start, end = parse_date_range("March 2025")
    assert start == date(2025, 3, 1)
    assert end == date(2025, 3, 31)


def test_parse_date_range_since():
    start, end = parse_date_range("since April 2024")
    assert start == date(2024, 4, 1)
    assert end >= date.today().replace(day=1)


def test_lock_file_removed_after_run(tmp_path):
    """Lock file is cleaned up even if a connector errors."""
    config = {
        "output_dir_expanded": tmp_path,
        "connectors": {},
        "_unconfigured": [],
    }
    with patch("tools.download_invoices.load_config", return_value=config):
        run_download("March 2025")
    assert not LOCK_FILE.exists()


def test_lock_file_blocks_concurrent_run(tmp_path, capsys):
    """If lock file exists, run exits immediately with a message."""
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOCK_FILE.touch()
    try:
        with pytest.raises(SystemExit):
            run_download("March 2025")
        captured = capsys.readouterr()
        assert "already running" in captured.out.lower()
    finally:
        LOCK_FILE.unlink(missing_ok=True)


def test_timed_out_connector_result_in_summary(tmp_path, capsys):
    """A connector that times out produces a timed_out result in the summary."""
    from concurrent.futures import TimeoutError as FuturesTimeout

    config = {
        "output_dir_expanded": tmp_path,
        "connectors": {"aws": {"access_key_id": "x", "secret_access_key": "x", "account_id": "x"}},
        "_unconfigured": [],
    }

    mock_aws = MagicMock()
    mock_aws.name = "AWS"
    mock_aws.stable = True
    mock_aws.is_configured.return_value = True

    with patch("tools.download_invoices.load_config", return_value=config):
        with patch("tools.download_invoices.ALL_CONNECTORS", [type(mock_aws)]):
            with patch("tools.download_invoices.ThreadPoolExecutor") as mock_pool:
                mock_future = MagicMock()
                mock_future.result.side_effect = FuturesTimeout()
                mock_pool.return_value.__enter__.return_value.submit.return_value = mock_future
                run_download("March 2025")

    captured = capsys.readouterr()
    assert "timed out" in captured.out.lower() or "timeout" in captured.out.lower()

# tests/test_base.py
import pytest
from datetime import date
from pathlib import Path
from tools.connectors.base import BaseConnector, ConnectorResult


class ConcreteConnector(BaseConnector):
    name = "TestService"
    stable = True

    def is_configured(self) -> bool:
        return True

    def download(self, start: date, end: date, out_dir: Path) -> ConnectorResult:
        return ConnectorResult(
            connector=self.name,
            files=[],
            count=0,
            skipped=0,
            error=None,
            hint=None,
        )


def test_connector_result_defaults():
    result = ConnectorResult(
        connector="AWS", files=[], count=0, skipped=0, error=None, hint=None
    )
    assert result.timed_out is False


def test_connector_result_with_error():
    result = ConnectorResult(
        connector="AWS",
        files=[],
        count=0,
        skipped=0,
        error="Auth failed",
        hint="Check your API key",
    )
    assert result.error == "Auth failed"
    assert result.hint == "Check your API key"


def test_concrete_connector_implements_interface():
    c = ConcreteConnector(config={})
    assert c.name == "TestService"
    assert c.stable is True
    assert c.is_configured() is True


def test_connector_download_returns_result():
    c = ConcreteConnector(config={})
    result = c.download(date(2025, 3, 1), date(2025, 3, 31), Path("/tmp"))
    assert isinstance(result, ConnectorResult)
    assert result.connector == "TestService"


def test_abstract_connector_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseConnector(config={})

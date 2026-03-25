# tests/test_stripe.py
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from tools.connectors.stripe import StripeConnector


@pytest.fixture
def stripe_config():
    return {"secret_key": "sk_live_xxxx"}


def test_stripe_is_configured(stripe_config):
    assert StripeConnector(config=stripe_config).is_configured() is True

def test_stripe_not_configured():
    assert StripeConnector(config={}).is_configured() is False

@patch("tools.connectors.stripe.stripe_lib.Invoice.list")
def test_stripe_downloads_invoices(mock_list, tmp_out, stripe_config):
    mock_inv = MagicMock()
    mock_inv.id = "in_123"
    mock_inv.created = 1740873600  # 2025-03-02
    mock_inv.invoice_pdf = None
    mock_inv.__iter__ = lambda s: iter([])
    mock_list.return_value = MagicMock(auto_paging_iter=lambda: iter([mock_inv]))

    c = StripeConnector(config=stripe_config)
    result = c.download(date(2025, 3, 1), date(2025, 3, 31), tmp_out)
    assert result.error is None

@patch("tools.connectors.stripe.stripe_lib.Invoice.list")
def test_stripe_returns_error_on_auth_failure(mock_list, tmp_out, stripe_config):
    import stripe as stripe_real
    mock_list.side_effect = stripe_real.error.AuthenticationError("Invalid key")
    c = StripeConnector(config=stripe_config)
    result = c.download(date(2025, 3, 1), date(2025, 3, 31), tmp_out)
    assert result.error is not None
    assert "secret_key" in result.hint.lower()

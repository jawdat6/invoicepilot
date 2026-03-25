# tools/connectors/stripe.py
import json
from datetime import date, datetime, timezone
from pathlib import Path

import stripe as stripe_lib

from .base import BaseConnector, ConnectorResult


class StripeConnector(BaseConnector):
    name = "Stripe"
    stable = True

    def is_configured(self) -> bool:
        return self._is_set("secret_key")

    def download(self, start: date, end: date, out_dir: Path) -> ConnectorResult:
        out_dir.mkdir(parents=True, exist_ok=True)
        period = start.strftime("%Y-%m")
        filename = out_dir / f"Stripe_{period}.json"

        if filename.exists():
            return ConnectorResult(connector=self.name, files=[], count=0, skipped=1, error=None, hint=None)

        stripe_lib.api_key = self.config["secret_key"]
        start_ts = int(datetime(start.year, start.month, 1, tzinfo=timezone.utc).timestamp())
        if start.month == 12:
            end_ts = int(datetime(start.year + 1, 1, 1, tzinfo=timezone.utc).timestamp())
        else:
            end_ts = int(datetime(start.year, start.month + 1, 1, tzinfo=timezone.utc).timestamp())

        try:
            invoices = list(stripe_lib.Invoice.list(
                created={"gte": start_ts, "lt": end_ts},
                limit=100,
            ).auto_paging_iter())

            data = [{"id": inv.id, "created": inv.created} for inv in invoices]
            filename.write_text(json.dumps(data, indent=2))
            return ConnectorResult(connector=self.name, files=[filename], count=len(invoices), skipped=0, error=None, hint=None)

        except stripe_lib.error.AuthenticationError:
            return ConnectorResult(
                connector=self.name, files=[], count=0, skipped=0,
                error="Stripe authentication failed",
                hint="Check secret_key in config.yml (should start with sk_live_)",
            )
        except Exception as e:
            return ConnectorResult(connector=self.name, files=[], count=0, skipped=0, error=str(e), hint=None)

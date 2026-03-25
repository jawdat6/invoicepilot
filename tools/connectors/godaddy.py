import json
from datetime import date
from pathlib import Path

import requests

from .base import BaseConnector, ConnectorResult


class GoDaddyConnector(BaseConnector):
    name = "GoDaddy"
    stable = True

    def is_configured(self) -> bool:
        return self._is_set("api_key", "api_secret")

    def download(self, start: date, end: date, out_dir: Path) -> ConnectorResult:
        out_dir.mkdir(parents=True, exist_ok=True)
        period = start.strftime("%Y-%m")
        orders_file = out_dir / f"GoDaddy_Orders_{period}.json"

        if orders_file.exists():
            return ConnectorResult(connector=self.name, files=[], count=0, skipped=1, error=None, hint=None)

        headers = {
            "Authorization": f"sso-key {self.config['api_key']}:{self.config['api_secret']}",
            "Accept": "application/json",
        }

        try:
            resp = requests.get("https://api.godaddy.com/v1/orders?pageSize=50", headers=headers, timeout=30)
            if resp.status_code in (401, 403):
                return ConnectorResult(
                    connector=self.name, files=[], count=0, skipped=0,
                    error="GoDaddy authentication failed",
                    hint="Ensure you are using a Production API key (not OTE/test). Check api_key in config.yml.",
                )
            resp.raise_for_status()

            data = resp.json()
            month_orders = [
                o for o in data.get("orders", [])
                if o.get("createdAt", "").startswith(period)
            ]

            orders_file.write_text(json.dumps(month_orders, indent=2))
            return ConnectorResult(connector=self.name, files=[orders_file], count=len(month_orders), skipped=0, error=None, hint=None)

        except Exception as e:
            return ConnectorResult(connector=self.name, files=[], count=0, skipped=0, error=str(e), hint=None)

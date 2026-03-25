import json
from datetime import date
from pathlib import Path

import requests

from .base import BaseConnector, ConnectorResult


class TwilioConnector(BaseConnector):
    name = "Twilio"
    stable = True

    def is_configured(self) -> bool:
        return self._is_set("account_sid", "auth_token")

    def download(self, start: date, end: date, out_dir: Path) -> ConnectorResult:
        out_dir.mkdir(parents=True, exist_ok=True)
        period = start.strftime("%Y-%m")
        filename = out_dir / f"Twilio_{period}.json"

        if filename.exists():
            return ConnectorResult(connector=self.name, files=[], count=0, skipped=1, error=None, hint=None)

        sid = self.config["account_sid"]
        token = self.config["auth_token"]

        if start.month == 12:
            end_date = f"{start.year + 1}-01-01"
        else:
            end_date = f"{start.year}-{start.month + 1:02d}-01"

        url = (
            f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Usage/Records/Monthly.json"
            f"?StartDate={start.strftime('%Y-%m-%d')}&EndDate={end_date}"
        )

        try:
            resp = requests.get(url, auth=(sid, token), timeout=30)
            if resp.status_code == 401:
                return ConnectorResult(
                    connector=self.name, files=[], count=0, skipped=0,
                    error="Twilio authentication failed",
                    hint="Check account_sid and auth_token in config.yml",
                )
            resp.raise_for_status()
            data = resp.json()
            filename.write_text(json.dumps(data, indent=2))
            return ConnectorResult(connector=self.name, files=[filename], count=1, skipped=0, error=None, hint=None)

        except Exception as e:
            return ConnectorResult(connector=self.name, files=[], count=0, skipped=0, error=str(e), hint=None)

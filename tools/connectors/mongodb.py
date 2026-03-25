import json
from datetime import date
from pathlib import Path

import requests
from requests.auth import HTTPDigestAuth

from .base import BaseConnector, ConnectorResult


class MongoDBConnector(BaseConnector):
    name = "MongoDB"
    stable = True

    def is_configured(self) -> bool:
        return self._is_set("public_key", "private_key", "org_id")

    def download(self, start: date, end: date, out_dir: Path) -> ConnectorResult:
        out_dir.mkdir(parents=True, exist_ok=True)
        period = start.strftime("%Y-%m")
        filename = out_dir / f"MongoDB_{period}.json"

        if filename.exists():
            return ConnectorResult(connector=self.name, files=[], count=0, skipped=1, error=None, hint=None)

        auth = HTTPDigestAuth(self.config["public_key"], self.config["private_key"])
        org_id = self.config["org_id"]
        url = f"https://cloud.mongodb.com/api/atlas/v2/orgs/{org_id}/invoices?itemsPerPage=100"
        headers = {"Accept": "application/vnd.atlas.2023-01-01+json"}

        try:
            resp = requests.get(url, auth=auth, headers=headers, timeout=30)
            if resp.status_code == 401:
                return ConnectorResult(
                    connector=self.name, files=[], count=0, skipped=0,
                    error="MongoDB Atlas authentication failed",
                    hint="Check public_key/private_key in config.yml. Key needs Organization Billing Viewer role.",
                )
            resp.raise_for_status()
            data = resp.json()
            invoices = [
                inv for inv in data.get("results", [])
                if inv.get("startDate", "")[:7] == period
            ]

            if not invoices:
                return ConnectorResult(connector=self.name, files=[], count=0, skipped=0, error=None, hint=None)

            filename.write_text(json.dumps(invoices, indent=2))
            return ConnectorResult(connector=self.name, files=[filename], count=len(invoices), skipped=0, error=None, hint=None)

        except Exception as e:
            return ConnectorResult(connector=self.name, files=[], count=0, skipped=0, error=str(e), hint=None)

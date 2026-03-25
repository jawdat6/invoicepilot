import json
import subprocess
from datetime import date
from pathlib import Path

import requests

from .base import BaseConnector, ConnectorResult


class GCloudConnector(BaseConnector):
    name = "Google Cloud"
    stable = True

    def _get_token(self) -> str | None:
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True, text=True,
        )
        return result.stdout.strip() if result.returncode == 0 else None

    def is_configured(self) -> bool:
        if not self._is_set("billing_account"):
            return False
        token = self._get_token()
        if not token:
            return False
        # Validate billing read access
        ba = self.config["billing_account"]
        resp = requests.get(
            f"https://cloudbilling.googleapis.com/v1/billingAccounts/{ba}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        return resp.status_code == 200

    def download(self, start: date, end: date, out_dir: Path) -> ConnectorResult:
        out_dir.mkdir(parents=True, exist_ok=True)
        period = start.strftime("%Y-%m")
        filename = out_dir / f"GCloud_{period}.json"

        if filename.exists():
            return ConnectorResult(connector=self.name, files=[], count=0, skipped=1, error=None, hint=None)

        token = self._get_token()
        if not token:
            return ConnectorResult(
                connector=self.name, files=[], count=0, skipped=0,
                error="Google Cloud ADC not found",
                hint="Run: gcloud auth application-default login",
            )

        ba = self.config["billing_account"]
        if start.month == 12:
            end_str = f"{start.year + 1}-01-01"
        else:
            end_str = f"{start.year}-{start.month + 1:02d}-01"

        summary = {
            "period": period,
            "billing_account": ba,
            "console_url": (
                f"https://console.cloud.google.com/billing/{ba}/reports"
                f"?dateRange=CUSTOM&from={period}-01&to={end_str}"
            ),
        }

        try:
            resp = requests.get(
                f"https://cloudbilling.googleapis.com/v1/billingAccounts/{ba}/projects?pageSize=50",
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
            if resp.status_code == 403:
                return ConnectorResult(
                    connector=self.name, files=[], count=0, skipped=0,
                    error="Google Cloud billing access denied",
                    hint=f"Grant roles/billing.viewer to your gcloud account on billing account {ba}",
                )
            summary["projects"] = resp.json()
            filename.write_text(json.dumps(summary, indent=2))
            return ConnectorResult(connector=self.name, files=[filename], count=1, skipped=0, error=None, hint=None)

        except Exception as e:
            return ConnectorResult(connector=self.name, files=[], count=0, skipped=0, error=str(e), hint=None)

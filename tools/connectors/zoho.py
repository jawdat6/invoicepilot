import json
from datetime import date
from pathlib import Path

import requests
import yaml

from .base import BaseConnector, ConnectorResult


class ZohoConnector(BaseConnector):
    name = "Zoho"
    stable = True

    def is_configured(self) -> bool:
        return self._is_set("client_id", "client_secret", "refresh_token")

    def _refresh_access_token(self) -> tuple[str, str | None]:
        """Returns (access_token, new_refresh_token_or_None)."""
        resp = requests.post(
            "https://accounts.zoho.com/oauth/v2/token",
            data={
                "refresh_token": self.config["refresh_token"],
                "client_id": self.config["client_id"],
                "client_secret": self.config["client_secret"],
                "grant_type": "refresh_token",
            },
            timeout=30,
        )
        data = resp.json()
        if resp.status_code != 200 or "access_token" not in data:
            raise ValueError(f"Token refresh failed: {data.get('error', 'unknown')}")
        return data["access_token"], data.get("refresh_token")

    def _save_new_refresh_token(self, new_token: str):
        """Atomically update refresh_token in config.yml using YAML parse + rewrite."""
        config_path = self.config.get("_config_path") or (Path.home() / ".invoicepilot" / "config.yml")
        try:
            with open(config_path) as f:
                data = yaml.safe_load(f)
            if data and "connectors" in data and "zoho" in data["connectors"]:
                data["connectors"]["zoho"]["refresh_token"] = new_token
                tmp = Path(str(config_path) + ".tmp")
                with open(tmp, "w") as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
                tmp.rename(config_path)
        except Exception:
            print("  Warning: Zoho refresh token rotated but could not be saved. Update refresh_token in config.yml manually.")

    def download(self, start: date, end: date, out_dir: Path) -> ConnectorResult:
        try:
            access_token, new_refresh = self._refresh_access_token()
            if new_refresh and new_refresh != self.config["refresh_token"]:
                self._save_new_refresh_token(new_refresh)
        except ValueError as e:
            return ConnectorResult(
                connector=self.name, files=[], count=0, skipped=0,
                error=str(e),
                hint="Check refresh_token, client_id, and client_secret in config.yml",
            )

        org_ids = self.config.get("org_ids") or {"default": self.config.get("org_id", "")}
        period = start.strftime("%Y-%m")
        files = []
        count = 0
        failed = 0

        for org_name, org_id in org_ids.items():
            if not org_id or org_id == "REPLACE_ME":
                continue
            org_dir = out_dir / org_name
            org_dir.mkdir(parents=True, exist_ok=True)

            page = 1
            while True:
                url = (
                    f"https://www.zohoapis.com/books/v3/invoices"
                    f"?organization_id={org_id}"
                    f"&date_after_equal={start.strftime('%Y-%m-%d')}"
                    f"&date_before_equal={end.strftime('%Y-%m-%d')}"
                    f"&sort_column=date&sort_order=A"
                    f"&page={page}&per_page=100"
                )
                try:
                    resp = requests.get(
                        url,
                        headers={
                            "Authorization": f"Zoho-oauthtoken {access_token}",
                            "X-com-zoho-books-organizationid": org_id,
                        },
                        timeout=30,
                    )
                    if resp.status_code == 429:
                        return ConnectorResult(
                            connector=self.name, files=files, count=count, skipped=0,
                            error="Zoho hit rate limit (1,000/day)",
                            hint="Try again tomorrow.",
                        )
                    data = resp.json()
                except Exception:
                    break

                invoices = data.get("invoices", [])
                if not invoices:
                    break

                for inv in invoices:
                    inv_id = inv["invoice_id"]
                    inv_date = inv.get("date", "unknown")[:7]
                    inv_num = inv.get("invoice_number", inv_id)
                    pdf_file = org_dir / f"Zoho_{org_name}_{inv_date}_{inv_num}.pdf"

                    if pdf_file.exists():
                        continue

                    try:
                        pdf_url = (
                            f"https://www.zohoapis.com/books/v3/invoices/{inv_id}"
                            f"?organization_id={org_id}&accept=pdf"
                        )
                        pdf_resp = requests.get(
                            pdf_url,
                            headers={"Authorization": f"Zoho-oauthtoken {access_token}"},
                            timeout=30,
                        )
                        pdf_file.write_bytes(pdf_resp.content)
                        files.append(pdf_file)
                        count += 1
                    except Exception:
                        failed += 1

                if not data.get("page_context", {}).get("has_more_page"):
                    break
                page += 1

        return ConnectorResult(connector=self.name, files=files, count=count, skipped=failed, error=None, hint=None)

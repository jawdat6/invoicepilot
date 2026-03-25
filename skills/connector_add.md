# InvoicePilot: Add Connector

You are adding a new invoice connector to InvoicePilot. You will read the service's API documentation, identify the billing/invoice endpoint, generate a working Python connector, and test it.

## Step 1: Gather information

Ask the user (one question at a time if not already provided):
1. **Service name** — what service are they connecting? (e.g. "Vercel", "Netlify", "Datadog")
2. **API docs** — URL to the billing/invoice API docs, OR paste of relevant docs
3. **Auth credentials** — what credentials do they have? (API key, token, client ID/secret, etc.)

If they've already provided this in their message, skip to Step 2.

## Step 2: Research the API

Use WebFetch to read the API docs URL they provided. Look for:
- The billing, invoice, or payment endpoint (e.g. `/v1/invoices`, `/billing/history`)
- Authentication method (Bearer token, Basic auth, API key header, OAuth)
- Response format — what fields contain invoice data, amounts, dates
- Any pagination patterns

If the docs URL doesn't have billing info, search for `{service} invoice API` or `{service} billing REST API`.

## Step 3: Generate the connector

Create `~/.invoicepilot/connectors/{service_lowercase}.py` following this exact pattern:

```python
import json
from datetime import date
from pathlib import Path

import requests  # or whatever the service needs

from tools.connectors.base import BaseConnector, ConnectorResult
# Note: if running as standalone, use:
# import sys; sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
# from connectors.base import BaseConnector, ConnectorResult


class {ServiceName}Connector(BaseConnector):
    name = "{ServiceName}"
    stable = True  # set False only if using Playwright

    def is_configured(self) -> bool:
        return self._is_set("{credential_key}")

    def download(self, start: date, end: date, out_dir: Path) -> ConnectorResult:
        out_dir.mkdir(parents=True, exist_ok=True)
        period = start.strftime("%Y-%m")
        filename = out_dir / f"{ServiceName}_{period}.json"

        if filename.exists():
            return ConnectorResult(
                connector=self.name, files=[], count=0, skipped=1, error=None, hint=None
            )

        try:
            # --- fetch invoices ---
            resp = requests.get(
                "https://api.{service}.com/v1/invoices",
                headers={"Authorization": f"Bearer {self.config['{credential_key}']}"},
                params={"start": start.isoformat(), "end": end.isoformat()},
                timeout=30,
            )
            if resp.status_code == 401:
                return ConnectorResult(
                    connector=self.name, files=[], count=0, skipped=0,
                    error="{ServiceName} authentication failed",
                    hint="Check {credential_key} in ~/.invoicepilot/config.yml",
                )
            resp.raise_for_status()
            data = resp.json()
            filename.write_text(json.dumps(data, indent=2))
            invoices = data.get("invoices") or data.get("data") or (data if isinstance(data, list) else [data])
            return ConnectorResult(
                connector=self.name, files=[filename],
                count=len(invoices), skipped=0, error=None, hint=None,
            )
        except Exception as e:
            return ConnectorResult(
                connector=self.name, files=[], count=0, skipped=0, error=str(e), hint=None,
            )
```

Adapt the actual API call, auth headers, response parsing, and date filtering to match what you found in the docs. The pattern above is a starting point — make it correct for the actual API.

## Step 4: Add credentials to config

Read `~/.invoicepilot/config.yml`. Add the new service credentials under `connectors:`:

```yaml
  {service_lowercase}:
    {credential_key}: REPLACE_ME    # description of where to get this
```

Tell the user to fill in the actual value.

## Step 5: Test

Run a quick sanity check:

```bash
python3 -c "
import sys
sys.path.insert(0, '$HOME/.claude/plugins/invoicepilot/tools')
sys.path.insert(0, '$HOME/.claude/plugins/invoicepilot')
from connectors import ALL_CONNECTORS
names = [c.name for c in ALL_CONNECTORS]
print('Loaded connectors:', names)
assert '{ServiceName}' in names, 'Connector not found!'
print('OK')
"
```

If the connector loads correctly, tell the user:

> ✓ **{ServiceName} connector added.**
>
> Fill in `{credential_key}` in `~/.invoicepilot/config.yml`, then say "download {ServiceName} invoices for last month" to test it.

If it fails, diagnose and fix before reporting success.

## What makes a good connector

- **Always check `filename.exists()` first** — skip if already downloaded (idempotent)
- **Always return `ConnectorResult`** — never raise, always catch and return error
- **Filter by month** — the orchestrator calls once per month, but some APIs return all invoices; filter to `start`..`end`
- **Error messages are for humans** — "Vercel auth failed. Check api_token in config.yml" not "401 Unauthorized"
- **Use `self._is_set()`** in `is_configured()` — handles None, empty string, and REPLACE_ME

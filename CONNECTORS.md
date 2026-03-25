# Writing InvoicePilot Connectors

InvoicePilot uses an open connector model: one Python file per service, all extending `BaseConnector`. The orchestrator automatically picks up any connector registered in `tools/connectors/__init__.py`.

## Quickstart

### 1. Create your connector file

Create `tools/connectors/myservice.py`:

```python
import json
from datetime import date
from pathlib import Path
import requests
from .base import BaseConnector, ConnectorResult


class MyServiceConnector(BaseConnector):
    name = "MyService"   # display name — shown in output and list
    stable = True        # set False if you use Playwright/browser automation

    def is_configured(self) -> bool:
        # Return True only if all required config keys are present and non-empty.
        # _is_set() handles None, "", and "REPLACE_ME" sentinel values automatically.
        return self._is_set("api_key")

    def download(self, start: date, end: date, out_dir: Path) -> ConnectorResult:
        out_dir.mkdir(parents=True, exist_ok=True)
        period = start.strftime("%Y-%m")
        filename = out_dir / f"MyService_{period}.json"

        # Always check for existing file first — idempotent by default
        if filename.exists():
            return ConnectorResult(
                connector=self.name, files=[], count=0, skipped=1, error=None, hint=None
            )

        try:
            resp = requests.get(
                "https://api.myservice.com/v1/invoices",
                headers={"Authorization": f"Bearer {self.config['api_key']}"},
                params={"start": start.isoformat(), "end": end.isoformat()},
                timeout=30,
            )
            if resp.status_code == 401:
                return ConnectorResult(
                    connector=self.name, files=[], count=0, skipped=0,
                    error="MyService authentication failed",
                    hint="Check api_key in ~/.invoicepilot/config.yml",
                )
            resp.raise_for_status()
            data = resp.json()
            filename.write_text(json.dumps(data, indent=2))
            return ConnectorResult(
                connector=self.name, files=[filename], count=len(data.get("invoices", [])),
                skipped=0, error=None, hint=None,
            )
        except Exception as e:
            return ConnectorResult(
                connector=self.name, files=[], count=0, skipped=0, error=str(e), hint=None,
            )
```

### 2. Register it

Add to `tools/connectors/__init__.py`:

```python
try:
    from .myservice import MyServiceConnector
    _connectors.append(MyServiceConnector)
except ImportError:
    pass
```

### 3. Add config keys

Add a section to the config template in `tools/init.py` (`CONFIG_TEMPLATE`):

```yaml
  myservice:
    api_key: REPLACE_ME
```

### 4. Write tests

Create `tests/test_myservice.py`:

```python
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from tools.connectors.myservice import MyServiceConnector

@pytest.fixture
def config():
    return {"api_key": "sk_test_123"}

def test_is_configured(config):
    assert MyServiceConnector(config=config).is_configured() is True

def test_not_configured_when_missing():
    assert MyServiceConnector(config={}).is_configured() is False

@patch("tools.connectors.myservice.requests.get")
def test_download_saves_json(mock_get, tmp_path, config):
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {"invoices": [{"id": "inv_1"}]},
    )
    result = MyServiceConnector(config=config).download(date(2025, 3, 1), date(2025, 3, 31), tmp_path)
    assert result.error is None
    assert result.count == 1

@patch("tools.connectors.myservice.requests.get")
def test_download_returns_error_on_401(mock_get, tmp_path, config):
    mock_get.return_value = MagicMock(status_code=401)
    result = MyServiceConnector(config=config).download(date(2025, 3, 1), date(2025, 3, 31), tmp_path)
    assert result.error is not None
    assert result.hint is not None
```

Run tests: `pytest tests/test_myservice.py -v`

### 5. Submit a PR

Open a PR to `jawdat6/invoicepilot` — we review and merge community connectors.

---

## BaseConnector Interface

```python
class BaseConnector(ABC):
    name: str           # Required. Display name, e.g. "Stripe"
    stable: bool = True # Set False for Playwright/browser connectors

    def __init__(self, config: dict):
        # config is the dict from config.yml under connectors.<service_key>

    def is_configured(self) -> bool:
        # Return True if all required keys are present, non-empty, non-REPLACE_ME
        # Use self._is_set("key1", "key2") for convenience

    def download(self, start: date, end: date, out_dir: Path) -> ConnectorResult:
        # Download invoices for ONE calendar month (start..end).
        # Called once per month by the orchestrator — do not handle date ranges internally.
        # Must complete within 60 seconds (120s for Playwright connectors).
```

## ConnectorResult

```python
@dataclass
class ConnectorResult:
    connector: str       # connector display name
    files: list[Path]    # files written (empty if skipped or error)
    count: int           # invoices downloaded
    skipped: int         # files that already existed (not overwritten)
    error: str | None    # None = success; set to human-readable error string
    hint: str | None     # actionable fix for the user (e.g. "Run: gcloud auth...")
    timed_out: bool = False
```

## Config Key Conventions

- Key in config.yml: lowercase service name with spaces removed (e.g. `googlecloud`, `myservice`)
- `_is_set(*keys)` checks: key present, not empty string, not `"REPLACE_ME"`
- For OAuth/refresh token connectors: store and update tokens atomically (see `zoho.py` for the pattern)

## Playwright Connectors

Set `stable = False` and handle `ImportError` gracefully:

```python
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

class MyPlaywrightConnector(BaseConnector):
    name = "MyService"
    stable = False

    def download(self, start, end, out_dir):
        if sync_playwright is None:
            return ConnectorResult(
                connector=self.name, files=[], count=0, skipped=0,
                error="Playwright not installed",
                hint="Run: pip install playwright && playwright install chromium",
            )
        ...
```

## Common Patterns

### Pagination

```python
results = []
page = 1
while True:
    resp = requests.get(url, params={"page": page, "per_page": 100}, ...)
    data = resp.json()
    results.extend(data["items"])
    if len(data["items"]) < 100:
        break
    page += 1
```

### Month boundary calculation

```python
from calendar import monthrange
last_day = monthrange(start.year, start.month)[1]
end_date = start.replace(day=last_day)
```

### December → January rollover

```python
if start.month == 12:
    next_month = date(start.year + 1, 1, 1)
else:
    next_month = date(start.year, start.month + 1, 1)
```

### PDF download

```python
resp = requests.get(pdf_url, headers=..., timeout=30, stream=True)
pdf_path = out_dir / f"MyService_{period}.pdf"
with open(pdf_path, "wb") as f:
    for chunk in resp.iter_content(chunk_size=8192):
        f.write(chunk)
```

## Requested Connectors

Open a GitHub issue with the label `connector-request` if you need a service that isn't supported yet. PRs welcome.

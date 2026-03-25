# InvoicePilot

Download all your SaaS invoices with one command.

InvoicePilot is a Claude Code plugin that downloads invoices from every connected SaaS service using natural language. No servers, no accounts — just a local config file and your existing API credentials.

## Supported Services

| Service | Method |
|---------|--------|
| AWS | Cost Explorer API |
| Twilio | Usage Records API |
| MongoDB Atlas | Atlas API v2 |
| Zoho Books | OAuth2 (auto token refresh) |
| GoDaddy | Orders API |
| Google Cloud | Cloud Billing API + ADC |
| Stripe | Invoices API |
| OpenPhone | Browser automation (⚠ unstable) |

## Installation

**Option A: Claude Plugin Marketplace**
```bash
claude plugin install invoicepilot
```

**Option B: Manual (git clone)**
```bash
git clone https://github.com/invoicepilot/invoicepilot ~/.claude/plugins/invoicepilot
```

**Setup (both options):**
```bash
# Create config file
invoicepilot init

# Edit credentials for the services you use
nano ~/.invoicepilot/config.yml

# Install Python dependencies
cd ~/.claude/plugins/invoicepilot
pip install -r requirements.txt

# (OpenPhone only) Install Playwright browser
playwright install chromium
```

## Usage

Open Claude Code and use natural language:

```
"download all invoices for last month"
"get invoices from April 2024 to now"
"check which services are connected"
"download only AWS and Stripe for Q1 2025"
```

## Example Output

```
InvoicePilot — Downloading March 2025

  ✓ AWS              3 invoices   → ~/Downloads/Invoices/2025-03/AWS/
  ✓ Twilio           1 invoice    → ~/Downloads/Invoices/2025-03/Twilio/
  ✓ MongoDB          1 invoice    → ~/Downloads/Invoices/2025-03/MongoDB/
  ✓ Zoho             4 invoices   → ~/Downloads/Invoices/2025-03/Zoho/
  ✓ GoDaddy          2 invoices   → ~/Downloads/Invoices/2025-03/GoDaddy/
  ✗ Google Cloud     Auth expired → Run: gcloud auth application-default login
  ✓ Stripe           1 invoice    → ~/Downloads/Invoices/2025-03/Stripe/
  ✓ OpenPhone ⚠      1 invoice    → ~/Downloads/Invoices/2025-03/OpenPhone/

  13 invoices downloaded. 1 skipped (already exists). 1 service needs attention.
  Folder: ~/Downloads/Invoices/2025-03/
```

## Config File

Config lives at `~/.invoicepilot/config.yml` (permissions: 600). Run `invoicepilot init` to generate the template.

Never commit this file — it contains credentials.

## Adding Connectors

Extend `BaseConnector` in `tools/connectors/`:

```python
from .base import BaseConnector, ConnectorResult

class MyServiceConnector(BaseConnector):
    name = "MyService"
    stable = True

    def is_configured(self) -> bool:
        return self._is_set("api_key")

    def download(self, start, end, out_dir):
        # fetch + save invoices
        return ConnectorResult(connector=self.name, ...)
```

Then add your connector class to `tools/connectors/__init__.py`.

## License

MIT

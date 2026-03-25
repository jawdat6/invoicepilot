import os
import sys
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".invoicepilot" / "config.yml"

CONFIG_TEMPLATE = """\
# InvoicePilot Configuration
# Run `invoicepilot init` to regenerate this template.
# This file contains credentials — do not commit it to git.
# Permissions should be 600 (chmod 600 ~/.invoicepilot/config.yml).

output_dir: ~/Downloads/Invoices

connectors:
  aws:
    # Required IAM permissions: ce:GetCostAndUsage, billing:GetBillingData
    access_key_id: REPLACE_ME
    secret_access_key: REPLACE_ME
    account_id: REPLACE_ME

  twilio:
    account_sid: REPLACE_ME      # ACxxxxxxxx
    auth_token: REPLACE_ME

  mongodb:
    public_key: REPLACE_ME
    private_key: REPLACE_ME      # UUID format
    org_id: REPLACE_ME

  zoho:
    # InvoicePilot will automatically update refresh_token after each use.
    client_id: REPLACE_ME        # 1000.xxxxxxxx
    client_secret: REPLACE_ME
    refresh_token: REPLACE_ME    # 1000.xxxxxxxx
    org_ids:
      default: REPLACE_ME
      # ksa: REPLACE_ME
      # sg: REPLACE_ME

  godaddy:
    api_key: REPLACE_ME
    api_secret: REPLACE_ME

  gcloud:
    billing_account: REPLACE_ME  # format: XXXXXX-XXXXXX-XXXXXX
    # Uses system Application Default Credentials.
    # Run: gcloud auth application-default login
    # Required role: roles/billing.viewer

  stripe:
    secret_key: REPLACE_ME       # sk_live_...

  openphone:
    # WARNING: Playwright-based. May break if OpenPhone changes login flow.
    email: REPLACE_ME
    password: REPLACE_ME
"""


def run_init(config_path: Path = DEFAULT_CONFIG_PATH):
    if config_path.exists():
        print(f"Config already exists at {config_path}. Edit it directly or delete it to re-initialize.")
        return

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(CONFIG_TEMPLATE)

    # Set permissions to 600 (owner read/write only)
    if sys.platform != "win32":
        os.chmod(config_path, 0o600)
    else:
        print("  Warning: file permissions cannot be enforced on Windows. Store config in a user-only directory.")

    print(f"Config created at {config_path}")
    print("Edit it to add your credentials, then run: invoicepilot list")


if __name__ == "__main__":
    run_init()

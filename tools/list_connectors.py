# tools/list_connectors.py
import sys
from pathlib import Path

# Ensure repo root is on the path so tools.connectors is importable when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.connectors import ALL_CONNECTORS
from tools.connectors.config import load_config, ConfigError

DEFAULT_CONFIG_PATH = Path.home() / ".invoicepilot" / "config.yml"


def run_list():
    try:
        config = load_config(DEFAULT_CONFIG_PATH)
    except ConfigError as e:
        print(f"Config error: {e}")
        sys.exit(1)

    connector_configs = config.get("connectors") or {}

    print("InvoicePilot — Connected Services\n")

    configured = []
    not_configured = []

    for cls in ALL_CONNECTORS:
        cfg = connector_configs.get(cls.name.lower().replace(" ", "")) or connector_configs.get(cls.name.lower()) or {}
        instance = cls(config=cfg)
        badge = " ⚠ unstable" if not instance.stable else ""
        if instance.is_configured():
            configured.append((instance.name, badge))
        else:
            not_configured.append(instance.name)

    for name, badge in configured:
        print(f"  ✓ {name}{badge}")

    if not_configured:
        print()
        for name in not_configured:
            print(f"  ○ {name}  (not configured)")

    print(f"\n  {len(configured)} connected, {len(not_configured)} not configured.")
    print(f"  Edit ~/.invoicepilot/config.yml to add more services.")


if __name__ == "__main__":
    run_list()

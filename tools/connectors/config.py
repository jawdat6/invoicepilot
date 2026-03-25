import yaml
from pathlib import Path

KNOWN_TOP_LEVEL_KEYS = {"output_dir", "connectors"}


class ConfigError(Exception):
    pass


def load_config(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}\nRun: invoicepilot init")

    try:
        with open(path) as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Config parse error in {path}:\n{e}")

    if raw is None:
        raw = {}

    # Warn on unknown top-level keys
    for key in raw:
        if key not in KNOWN_TOP_LEVEL_KEYS:
            print(f"  Warning: unknown key '{key}' in config.yml (possible typo)")

    connectors = raw.get("connectors") or {}

    # Detect REPLACE_ME sentinels — mark connector as unconfigured
    unconfigured = []
    for service, values in connectors.items():
        if isinstance(values, dict):
            if all(v == "REPLACE_ME" for v in values.values()):
                unconfigured.append(service)

    raw["_unconfigured"] = unconfigured

    # Expand output_dir tilde
    output_dir = raw.get("output_dir", "~/Downloads/Invoices")
    raw["output_dir_expanded"] = Path(output_dir).expanduser()

    return raw

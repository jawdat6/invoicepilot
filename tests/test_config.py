# tests/test_config.py
import pytest
import tempfile
from pathlib import Path
from tools.connectors.config import load_config, ConfigError

VALID_YAML = """
output_dir: ~/Downloads/Invoices
connectors:
  aws:
    access_key_id: AKIAXXXXXXXX
    secret_access_key: mysecret
    account_id: "123456789012"
  twilio:
    account_sid: ACxxxxxxxx
    auth_token: mytoken
"""

REPLACE_ME_YAML = """
output_dir: ~/Downloads/Invoices
connectors:
  aws:
    access_key_id: REPLACE_ME
    secret_access_key: REPLACE_ME
    account_id: REPLACE_ME
"""

MALFORMED_YAML = """
output_dir: ~/Downloads/Invoices
connectors:
  aws:
    bad: [unclosed
"""

UNKNOWN_KEYS_YAML = """
output_dir: ~/Downloads/Invoices
typo_key: oops
connectors: {}
"""


def write_config(content: str) -> Path:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(content)
        path = Path(f.name)
    return path


def test_load_valid_config():
    path = write_config(VALID_YAML)
    config = load_config(path)
    assert config["output_dir"] == "~/Downloads/Invoices"
    assert config["connectors"]["aws"]["access_key_id"] == "AKIAXXXXXXXX"


def test_replace_me_values_not_in_configured():
    path = write_config(REPLACE_ME_YAML)
    config = load_config(path)
    # REPLACE_ME values should be loaded but flagged
    assert config["connectors"]["aws"]["access_key_id"] == "REPLACE_ME"
    assert config["_unconfigured"] == ["aws"]


def test_malformed_yaml_raises_config_error():
    path = write_config(MALFORMED_YAML)
    with pytest.raises(ConfigError) as exc_info:
        load_config(path)
    assert "parse error" in str(exc_info.value).lower()


def test_unknown_top_level_keys_warns(capsys):
    path = write_config(UNKNOWN_KEYS_YAML)
    load_config(path)
    captured = capsys.readouterr()
    assert "typo_key" in captured.out or "unknown" in captured.out.lower()


def test_missing_config_file_raises_config_error():
    with pytest.raises(ConfigError) as exc_info:
        load_config(Path("/nonexistent/config.yml"))
    assert "not found" in str(exc_info.value).lower()


def test_output_dir_tilde_expanded():
    path = write_config(VALID_YAML)
    config = load_config(path)
    assert "~" not in str(config["output_dir_expanded"])

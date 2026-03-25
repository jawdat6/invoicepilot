import os
import stat
import pytest
from pathlib import Path
from unittest.mock import patch
from tools.init import run_init

CONFIG_TEMPLATE_KEYS = [
    "output_dir",
    "access_key_id",
    "account_sid",
    "public_key",
    "refresh_token",
    "billing_account",
    "secret_key",
]


def test_init_creates_config_file(tmp_path):
    config_path = tmp_path / "config.yml"
    run_init(config_path=config_path)
    assert config_path.exists()


def test_init_config_contains_replace_me(tmp_path):
    config_path = tmp_path / "config.yml"
    run_init(config_path=config_path)
    content = config_path.read_text()
    assert "REPLACE_ME" in content


def test_init_config_contains_all_sections(tmp_path):
    config_path = tmp_path / "config.yml"
    run_init(config_path=config_path)
    content = config_path.read_text()
    for key in CONFIG_TEMPLATE_KEYS:
        assert key in content, f"Missing key: {key}"


def test_init_sets_file_permissions_600(tmp_path):
    config_path = tmp_path / "config.yml"
    run_init(config_path=config_path)
    mode = oct(stat.S_IMODE(os.stat(config_path).st_mode))
    assert mode == "0o600"


def test_init_does_not_overwrite_existing_config(tmp_path, capsys):
    config_path = tmp_path / "config.yml"
    config_path.write_text("existing: content")
    run_init(config_path=config_path)
    assert config_path.read_text() == "existing: content"
    captured = capsys.readouterr()
    assert "already exists" in captured.out.lower()

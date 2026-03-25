from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass
class ConnectorResult:
    connector: str
    files: list
    count: int
    skipped: int
    error: str | None
    hint: str | None
    timed_out: bool = False


class BaseConnector(ABC):
    name: str = ""
    stable: bool = True

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if all required config keys are present and non-empty."""

    @abstractmethod
    def download(self, start: date, end: date, out_dir: Path) -> ConnectorResult:
        """Download invoices for a single calendar month into out_dir."""

    def _is_set(self, *keys: str) -> bool:
        """Return True if all keys exist in config and are not REPLACE_ME."""
        for key in keys:
            val = self.config.get(key, "")
            if not val or val == "REPLACE_ME":
                return False
        return True

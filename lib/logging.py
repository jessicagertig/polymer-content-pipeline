"""Structured logging — pretty console for CLI, JSON-friendly format for daemons."""

import logging
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler


_CONFIGURED = False


def setup(level: str = "INFO", log_file: Optional[Path] = None) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    handlers: list[logging.Handler] = [
        RichHandler(rich_tracebacks=True, show_time=True, show_path=False, markup=True)
    ]

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
        )
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%H:%M:%S]",
        handlers=handlers,
    )

    # Quiet noisy dependencies
    for noisy in ("httpx", "urllib3", "googleapiclient.discovery_cache", "anthropic"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


def get(name: str) -> logging.Logger:
    if not _CONFIGURED:
        setup()
    return logging.getLogger(name)


class ListHandler(logging.Handler):
    """Collects formatted log records in memory instead of writing them anywhere —
    used to relay an entire run's log to Slack, since Cloud Run Jobs only surface
    logs in Cloud Logging otherwise."""

    def __init__(self):
        super().__init__()
        self.records: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        # One line per record for the Slack report: the message only, no traceback.
        message = " ".join(line.strip() for line in record.getMessage().splitlines() if line.strip())
        self.records.append(f"{record.levelname}: {message[:300]}")


def capture_to_list(level: str = "INFO") -> ListHandler:
    """Attaches a ListHandler to the root logger and returns it. Call `release()`
    with the returned handler when the run is over."""
    handler = ListHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    root = logging.getLogger()
    # Force the root logger's own threshold down too — something else (e.g. a test
    # runner's log-capturing plugin) may have raised it above what we need here.
    if root.level == logging.NOTSET or root.level > handler.level:
        root.setLevel(handler.level)
    root.addHandler(handler)
    return handler


def release(handler: ListHandler) -> None:
    logging.getLogger().removeHandler(handler)

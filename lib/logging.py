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

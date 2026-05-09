"""Logging bootstrap: rotating file (DEBUG) + Rich console (WARNING)."""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler


def setup_logging(log_file: str | None = None, _log_level: str | None = None) -> None:
    """
    Attach a rotating DEBUG file handler and a Rich WARN+ console handler to the root logger.
    Clears duplicate root handlers before reconfiguring.
    """
    file_path_str: str = log_file or os.getenv("LOG_FILE") or "logs/trading_bot.log"

    Path(file_path_str).parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.DEBUG)

    rotating = RotatingFileHandler(
        file_path_str,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    rotating.setLevel(logging.DEBUG)
    rotating.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s — %(message)s"))

    console = RichHandler(show_path=False, rich_tracebacks=True)
    console.setLevel(logging.WARNING)
    console.setFormatter(logging.Formatter("%(message)s"))

    root.addHandler(rotating)
    root.addHandler(console)

    logging.captureWarnings(True)
    logging.getLogger(__name__).debug(
        "Logging configured: file=%s file_level=DEBUG console_level=WARNING",
        file_path_str,
    )

"""Centralized logging configuration."""

from __future__ import annotations

import logging
import os
from logging import Logger

from rich.logging import RichHandler

CONFIGURED = False
NOISY_LOGGERS = ("urllib3", "httpx", "sentence_transformers", "weaviate")


def log_level() -> int:
    """Resolve the configured log level from the environment."""
    level_name = os.environ.get("MDAD_LOG_LEVEL", "INFO").upper()
    return int(getattr(logging, level_name, logging.INFO))


def handlers_and_format() -> tuple[list[logging.Handler], str]:
    """Build the root logging handlers and message format."""
    if RichHandler is not None:
        return [RichHandler(rich_tracebacks=True, show_time=True, show_path=False)], "%(message)s"
    return [logging.StreamHandler()], "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def quiet_third_party_loggers() -> None:
    """Reduce noise from verbose dependency loggers."""
    for name in NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


def configure_root() -> None:
    """Configure the root logger once."""
    global CONFIGURED
    if CONFIGURED:
        return

    handlers, fmt = handlers_and_format()
    logging.basicConfig(level=log_level(), format=fmt, datefmt="%H:%M:%S", handlers=handlers, force=True)
    quiet_third_party_loggers()
    CONFIGURED = True


def get_logger(name: str) -> Logger:
    """Return a configured logger with the given name."""
    configure_root()
    return logging.getLogger(name)

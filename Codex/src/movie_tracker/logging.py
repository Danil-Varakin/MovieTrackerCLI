from __future__ import annotations

import sys

from loguru import logger

from movie_tracker.config import AppConfig


def setup_logging(config: AppConfig, *, verbose: bool = False, quiet: bool = False) -> None:
    logger.remove()
    level = "DEBUG" if verbose else config.data["logging"].get("level", "WARNING")
    if quiet:
        level = "ERROR"

    config.log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(sys.stderr, level=level, colorize=True, backtrace=False, diagnose=False)
    logger.add(
        config.log_path,
        level=level,
        rotation=config.data["logging"].get("rotation", "10 MB"),
        retention=config.data["logging"].get("retention", "30 days"),
        serialize=True,
        backtrace=False,
        diagnose=False,
    )

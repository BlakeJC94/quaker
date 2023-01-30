"""Logging functions"""
import logging


def setup_logging():
    """Logger setup."""
    log_level = logging.WARNING

    logger = logging.getLogger()
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s: %(message)s",
        level=log_level,
        force=True,
    )
    return logger

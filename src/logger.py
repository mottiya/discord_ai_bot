import logging

from src.settings import Settings


def setup_logging(settings: Settings):
    logging.basicConfig(
        level=settings.log_level,
        format=settings.log_format,
        filename=settings.log_file,
    )

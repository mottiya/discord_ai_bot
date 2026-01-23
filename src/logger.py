import logging

from src.settings import Settings


def setup_logging(settings: Settings):
    file_handler = logging.FileHandler(settings.log_file, encoding="utf-8")
    file_handler.setLevel(settings.log.level)
    file_handler.setFormatter(logging.Formatter(settings.log.format))

    logging.basicConfig(
        level=settings.log.level,
        format=settings.log.format,
        handlers=[file_handler],
    )

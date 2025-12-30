import logging

from src.settings import Settings


def setup_logging(settings: Settings):
    # Настраиваем FileHandler с явным указанием кодировки UTF-8
    file_handler = logging.FileHandler(settings.log_file, encoding='utf-8')
    file_handler.setLevel(settings.log_level)
    file_handler.setFormatter(logging.Formatter(settings.log_format))

    # Настраиваем базовую конфигурацию без файла, чтобы добавить handler вручную
    logging.basicConfig(
        level=settings.log_level,
        format=settings.log_format,
        handlers=[file_handler],
    )

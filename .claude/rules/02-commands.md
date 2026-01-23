# Команды

```bash
# Запуск бота
uv run python -m src.main

# Запуск всех тестов
uv run pytest

# Запуск одного файла тестов
uv run pytest tests/test_settings.py

# Запуск конкретного теста
uv run pytest tests/test_settings.py::test_name -v

# Линтинг и форматирование
uv run ruff check .
uv run ruff format .

# Проверка типов
uv run mypy src/
```

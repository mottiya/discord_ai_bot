# Переменные окружения

Обязательные переменные (см. `.env.example`):
- `DBA__DISCORD__CHANNEL_ID` - Целевой Discord-канал
- `DBA__DISCORD__IDENTITY_1__ID`, `DBA__DISCORD__IDENTITY_1__TOKEN` - Первая личность бота
- `DBA__DISCORD__IDENTITY_2__ID`, `DBA__DISCORD__IDENTITY_2__TOKEN` - Вторая личность бота
- `DBA__MAIN_AI__MODEL`, `DBA__MAIN_AI__API_KEY` - Конфигурация модели ИИ

Опциональные переменные:
- `DBA__SESSION_TIMEOUT` - Таймаут сессии в секундах (по умолчанию 1200)
- `DBA__MAIN_AI__TEMPERATURE` - Температура модели (по умолчанию 0.7)
- `DBA__MAIN_AI__MAX_TOKENS` - Максимум токенов (по умолчанию 1000)
- `DBA__MAIN_AI__TOP_P` - Top-p sampling (по умолчанию 1.0)
- `DBA__LOG__LEVEL` - Уровень логирования (10/20/30/40/50, по умолчанию 20)
- `DBA__LOG__FILENAME` - Имя файла лога (по умолчанию app.log)

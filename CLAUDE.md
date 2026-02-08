# Telegram-бот: генератор идей для вайб-кодинга

Бот помогает экспертам и предпринимателям найти идеи для веб-приложений через AI (OpenRouter API).

## Критические правила

- **НЕ коммить `.env`** — содержит `TELEGRAM_BOT_TOKEN` и `OPENROUTER_API_KEY`
- **HTML-разметка в ответах** — бот использует `parse_mode="HTML"`, НЕ Markdown
- **Промпт в `prompts.py`** — длинный системный промпт (~260 строк), правки аккуратно
- **Маркер идей** — строка `"Какая идея зацепила"` в ответе LLM триггерит отправку картинки + кнопок + продающего блока

## Команды

- `python bot.py` — запуск бота (polling mode)
- `python check_bot_status.py` — проверка статуса бота через Telegram API
- `pip install -r requirements.txt` — установка зависимостей

## Архитектура

| Файл | Назначение |
|------|------------|
| `bot.py` | Основной файл: хендлеры aiogram, FSM, inline-кнопки |
| `llm.py` | Клиент OpenRouter API (`OpenRouterClient`) |
| `prompts.py` | Системный промпт для LLM (SYSTEM_PROMPT) |
| `logger.py` | Логирование диалогов в `logs/conversations.log` |
| `check_bot_status.py` | Утилита проверки бота (getMe, webhook, updates) |
| `vibes_image.jpg` | Картинка, отправляемая вместе с идеями |

## Ключевые паттерны

**FSM**: `ConversationState.chatting` — единственное состояние, история хранится в `state.data["history"]` (последние 10 сообщений).

**Анимация "думает"**: `animate_thinking()` — циклически меняет текст сообщения пока LLM генерирует ответ. Всегда отменяй `animation_task` перед отправкой ответа.

**Inline-кнопки**: `idea_1`..`idea_4` — callback для раскрытия идей; кнопка "Узнать про ВАЙБС" — внешняя ссылка.

**Отложенная отправка**: `send_live_stream_link()` — ссылка на стрим отправляется через 1 час (3600 сек) после генерации идей.

## Переменные окружения

| Переменная | Обязательная | Описание |
|------------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Да | Токен от @BotFather |
| `OPENROUTER_API_KEY` | Да | Ключ OpenRouter API |
| `LIVE_STREAM_URL` | Нет | Ссылка на YouTube-стрим (есть дефолт) |

## Стек

Python 3.9, aiogram 3.15, httpx 0.28, python-dotenv. Деплой на Railway (`Procfile`: `worker: python3 bot.py`).

## LLM

Модель: `stepfun/step-3.5-flash:free` через OpenRouter. Timeout: 120 сек, temperature: 0.7, max_tokens: 4000.

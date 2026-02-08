# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Описание

Telegram-бот: генератор идей для вайб-кодинга. Помогает экспертам и предпринимателям найти идеи для веб-приложений через AI (OpenRouter API).

## Команды

- `python bot.py` — запуск бота (polling mode)
- `python check_bot_status.py` — проверка статуса бота через Telegram API
- `pip install -r requirements.txt` — установка зависимостей

## Критические правила

- **НЕ коммить `.env`** — содержит `TELEGRAM_BOT_TOKEN` и `OPENROUTER_API_KEY`
- **HTML-разметка в ответах** — бот использует `parse_mode="HTML"`, НЕ Markdown. Допустимые теги: `<b>`, `<i>`. Запрещены: `<u>`, `<code>`, `<s>`, разделители (`──`, `===`)
- **Промпт в `prompts.py`** — длинный системный промпт (~260 строк), правки аккуратно
- **Маркер идей** — строка `"Какая идея зацепила"` в ответе LLM триггерит отправку картинки + кнопок + продающего блока. Если убрать/изменить — сломается вся цепочка
- **Анимация "думает"** — `animation_task` ОБЯЗАТЕЛЬНО отменять (`cancel()`) и удалять сообщение перед отправкой ответа, иначе ответ не дойдёт

## Архитектура

| Файл | Назначение |
|------|------------|
| `bot.py` | Хендлеры aiogram, FSM, inline-кнопки, анимация "думает" |
| `llm.py` | Клиент OpenRouter API (`OpenRouterClient`) |
| `prompts.py` | Системный промпт для LLM (`SYSTEM_PROMPT`) |
| `logger.py` | Логирование диалогов в `logs/conversations.log` |
| `check_bot_status.py` | Утилита проверки бота (getMe, webhook, updates) |
| `vibes_image.jpg` | Картинка, отправляемая вместе с идеями |

## Ключевые паттерны

**FSM**: `ConversationState.chatting` — единственное состояние, история хранится в `state.data["history"]` (последние 10 сообщений).

**Триггерная цепочка при генерации идей**: LLM ответ содержит `"Какая идея зацепила"` → отправка `vibes_image.jpg` → текст идей с inline-кнопками (`idea_1`..`idea_4`) → продающий блок с кнопкой "Узнать про ВАЙБС" → через 1 час отправка ссылки на стрим (`send_live_stream_link()`).

**Inline-кнопки**: `idea_1`..`idea_4` — callback для раскрытия идей с детальной разбивкой (как работает, проблема, монетизация).

## Переменные окружения

| Переменная | Обязательная | Описание |
|------------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Да | Токен от @BotFather |
| `OPENROUTER_API_KEY` | Да | Ключ OpenRouter API |
| `LIVE_STREAM_URL` | Нет | Ссылка на YouTube-стрим (есть дефолт) |

## Стек

Python 3.9, aiogram 3.15, httpx 0.28, python-dotenv. Деплой на Railway (`Procfile`: `worker: python3 bot.py`).

## LLM

Модель: `google/gemini-3-flash-preview` через OpenRouter. Timeout: 120 сек, temperature: 0.7, max_tokens: 4000.

"""Модуль для логирования диалогов с пользователями."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


# Создаём директорию для логов, если её нет
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Настраиваем логгер
logger = logging.getLogger("vibecoding_bot")
logger.setLevel(logging.INFO)

# Создаём handler для записи в файл
file_handler = logging.FileHandler(
    LOGS_DIR / "conversations.log",
    encoding="utf-8"
)
file_handler.setLevel(logging.INFO)

# Формат лога: [2025-01-15 14:32:01] user_id=123456 username=@ivan_petrov message="..." response="..."
formatter = logging.Formatter(
    "[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


def log_conversation(
    user_id: int,
    username: Optional[str],
    message: str,
    response: str
) -> None:
    """
    Логирует диалог с пользователем.

    Args:
        user_id: Telegram ID пользователя
        username: Username пользователя (может быть None)
        message: Сообщение от пользователя
        response: Ответ бота
    """
    username_str = f"@{username}" if username else "no_username"

    # Экранируем кавычки в сообщениях
    message_escaped = message.replace('"', '\\"')
    response_escaped = response.replace('"', '\\"')

    log_entry = (
        f'user_id={user_id} '
        f'username={username_str} '
        f'message="{message_escaped}" '
        f'response="{response_escaped}"'
    )

    logger.info(log_entry)

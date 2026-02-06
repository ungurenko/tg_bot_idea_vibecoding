"""Модуль для работы с OpenRouter API."""

import httpx
from typing import List, Dict
from prompts import SYSTEM_PROMPT


class LLMError(Exception):
    """Исключение при ошибке работы с LLM."""
    pass


class OpenRouterClient:
    """Клиент для работы с OpenRouter API."""

    def __init__(self, api_key: str):
        """
        Инициализирует клиент.

        Args:
            api_key: API ключ для OpenRouter
        """
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "stepfun/step-3.5-flash:free"
        self.timeout = 120.0

    async def get_response(self, user_message: str, history: List[Dict[str, str]] = None) -> str:
        """
        Получает ответ от LLM.

        Args:
            user_message: Сообщение от пользователя
            history: История диалога (опционально)

        Returns:
            Ответ от LLM

        Raises:
            LLMError: При ошибке запроса к API
        """
        # Формируем историю сообщений
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        # Добавляем историю, если есть
        if history:
            messages.extend(history)

        # Добавляем текущее сообщение
        messages.append({"role": "user", "content": user_message})

        # Формируем тело запроса
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4000
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers=headers
                )

                response.raise_for_status()
                data = response.json()

                # Извлекаем ответ из response
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    raise LLMError("Неожиданный формат ответа от API")

        except httpx.TimeoutException:
            raise LLMError("Превышено время ожидания ответа от LLM")
        except httpx.HTTPStatusError as e:
            body = e.response.text[:200]
            raise LLMError(f"HTTP {e.response.status_code}: {body}")
        except httpx.RequestError as e:
            raise LLMError(f"Ошибка соединения: {str(e)}")
        except Exception as e:
            raise LLMError(f"Неизвестная ошибка: {str(e)}")

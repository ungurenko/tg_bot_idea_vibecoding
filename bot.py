"""Основной файл Telegram-бота для генерации идей вайб-кодинга."""

import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from dotenv import load_dotenv

from llm import OpenRouterClient, LLMError
from logger import log_conversation


# Загружаем переменные окружения
load_dotenv()

# Получаем токены из окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LIVE_STREAM_URL = os.getenv("LIVE_STREAM_URL", "https://www.youtube.com/live/iOnk4zozyw8?si=qByw0py3KYdjAIji")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен в .env файле")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY не установлен в .env файле")

# Инициализируем бот и диспетчер
bot = Bot(token=TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Инициализируем LLM клиент
llm_client = OpenRouterClient(api_key=OPENROUTER_API_KEY)


class ConversationState(StatesGroup):
    """Состояния диалога."""
    chatting = State()


def create_vibes_button() -> InlineKeyboardMarkup:
    """
    Создаёт кнопку со ссылкой на обучение ВАЙБС.

    Returns:
        InlineKeyboardMarkup с кнопкой
    """
    button = InlineKeyboardButton(
        text="🚀 Узнать про ВАЙБС",
        url="https://vibes-landing-gamma.vercel.app/"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
    return keyboard


async def send_live_stream_link(chat_id: int, delay_seconds: int = 60) -> None:
    """
    Отправляет ссылку на прямой эфир после задержки.

    Args:
        chat_id: ID чата для отправки сообщения
        delay_seconds: Задержка перед отправкой в секундах (по умолчанию 60)
    """
    await asyncio.sleep(delay_seconds)
    
    message = (
        "🎓 Хочешь научиться вайб-кодингу бесплатно?\n\n"
        "Заглядывай на мой прямой эфир — там я показываю всё на практике и помогаю разобраться!\n\n"
        f"▶️ {LIVE_STREAM_URL}"
    )
    
    await bot.send_message(chat_id=chat_id, text=message)


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик команды /start.

    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
    """
    # Очищаем историю при старте
    await state.clear()
    await state.set_state(ConversationState.chatting)

    welcome_message = (
        "<b>Привет!</b> 👋 Я помогу тебе найти идеи для <i>вайб-кодинга</i> в твоей нише. "
        "Расскажи, чем ты занимаешься — какая у тебя сфера или экспертиза?"
    )

    await message.answer(welcome_message, parse_mode="HTML")

    # Логируем приветствие
    log_conversation(
        user_id=message.from_user.id,
        username=message.from_user.username,
        message="/start",
        response=welcome_message
    )


@dp.message(F.text)
async def handle_message(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик текстовых сообщений.

    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
    """
    user_message = message.text

    # Получаем историю диалога из состояния
    data = await state.get_data()
    history = data.get("history", [])

    try:
        # Отправляем сообщение "думаю..."
        thinking_msg = await message.answer(
            "Так, тут нужно <i>подумать</i>, дай мне немного времени... 🤔",
            parse_mode="HTML"
        )

        # Отправляем индикатор набора текста
        await message.bot.send_chat_action(
            chat_id=message.chat.id,
            action="typing"
        )

        # Получаем ответ от LLM
        response = await llm_client.get_response(user_message, history)

        # Удаляем сообщение "думаю..."
        await thinking_msg.delete()

        # Проверяем, нужна ли кнопка ВАЙБС (если в ответе есть идеи)
        if "ВАЙБС" in response and "Хочешь реализовать" in response:
            # Сначала отправляем картинку из локального файла
            photo_path = os.path.join(os.path.dirname(__file__), "vibes_image.jpg")
            photo = FSInputFile(photo_path)
            await message.answer_photo(photo=photo)
            # Потом отправляем текст с идеями и кнопкой
            await message.answer(response, parse_mode="HTML", reply_markup=create_vibes_button())
            
            # Запускаем отложенную задачу для отправки ссылки на эфир через 1 минуту
            asyncio.create_task(send_live_stream_link(message.chat.id, delay_seconds=60))
        else:
            # Отправляем ответ без кнопки
            await message.answer(response, parse_mode="HTML")

        # Обновляем историю диалога
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": response})

        # Сохраняем историю (ограничиваем последними 10 сообщениями)
        await state.update_data(history=history[-10:])

        # Логируем диалог
        log_conversation(
            user_id=message.from_user.id,
            username=message.from_user.username,
            message=user_message,
            response=response
        )

    except LLMError as e:
        # Проверяем тип ошибки для более точного сообщения
        if "429" in str(e):
            error_message = "<b>Упс, слишком много запросов!</b> Подожди минутку и попробуй снова ⏱️"
        else:
            error_message = "<b>Что-то пошло не так</b>, попробуй ещё раз через минуту 🔄"

        await message.answer(error_message, parse_mode="HTML")

        # Логируем ошибку
        log_conversation(
            user_id=message.from_user.id,
            username=message.from_user.username,
            message=user_message,
            response=f"ERROR: {str(e)}"
        )


async def main():
    """Запуск бота."""
    print("🤖 Бот запущен и готов к работе!")
    print("Нажмите Ctrl+C для остановки")

    try:
        # Удаляем webhook на случай если был установлен
        await bot.delete_webhook(drop_pending_updates=True)
        # Запускаем polling
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")

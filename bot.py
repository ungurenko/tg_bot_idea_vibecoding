"""Основной файл Telegram-бота для генерации идей вайб-кодинга."""

import asyncio
import logging
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

# Логгер ошибок в файл (для отладки на сервере: cat logs/errors.log)
error_logger = logging.getLogger("error_debug")
error_logger.setLevel(logging.ERROR)
_err_handler = logging.FileHandler("logs/errors.log", encoding="utf-8")
_err_handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
error_logger.addHandler(_err_handler)

# Загружаем переменные окружения
load_dotenv()

# Получаем токены из окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LIVE_STREAM_URL = os.getenv("LIVE_STREAM_URL", "https://www.youtube.com/live/iOnk4zozyw8?si=qByw0py3KYdjAIji")

# Диагностика для Railway
print("🔍 Проверка переменных окружения:")
print(f"TELEGRAM_BOT_TOKEN установлен: {'✅' if TELEGRAM_BOT_TOKEN else '❌'}")
print(f"OPENROUTER_API_KEY установлен: {'✅' if OPENROUTER_API_KEY else '❌'}")
print(f"LIVE_STREAM_URL: {LIVE_STREAM_URL}")

if not TELEGRAM_BOT_TOKEN:
    print("❌ Ошибка: TELEGRAM_BOT_TOKEN не найден!")
    print("Доступные переменные окружения (начинающиеся с TELEGRAM):")
    for key in os.environ:
        if 'TELEGRAM' in key.upper():
            print(f"  - {key}")
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения")

if not OPENROUTER_API_KEY:
    print("❌ Ошибка: OPENROUTER_API_KEY не найден!")
    print("Доступные переменные окружения (начинающиеся с OPENROUTER):")
    for key in os.environ:
        if 'OPENROUTER' in key.upper():
            print(f"  - {key}")
    raise ValueError("OPENROUTER_API_KEY не установлен в переменных окружения")

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
    """Создаёт кнопку со ссылкой на обучение ВАЙБС."""
    button = InlineKeyboardButton(
        text="🚀 Узнать про ВАЙБС",
        url="https://vibes-landing-gamma.vercel.app/"
    )
    return InlineKeyboardMarkup(inline_keyboard=[[button]])


def create_idea_buttons(count: int = 4) -> InlineKeyboardMarkup:
    """Создаёт кнопки выбора идей 💡 1-N."""
    buttons = [
        InlineKeyboardButton(text=f"💡 {i}", callback_data=f"idea_{i}")
        for i in range(1, count + 1)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


THINKING_STAGES = [
    "Анализирую твою нишу... 🔍",
    "Подбираю идеи под тебя... 💡",
    "Оцениваю потенциал проектов... 📊",
    "Формулирую рекомендации... ✍️",
    "Почти готово... ✨",
]


async def animate_thinking(message: types.Message, interval: float = 3.0):
    """Циклически меняет текст сообщения, пока LLM думает."""
    try:
        stage = 0
        while True:
            await asyncio.sleep(interval)
            text = THINKING_STAGES[stage % len(THINKING_STAGES)]
            try:
                await message.edit_text(text, parse_mode="HTML")
            except Exception:
                pass
            stage += 1
    except asyncio.CancelledError:
        pass


VIBES_SALES_TEXT = (
    "🚀 <b>Хочешь реализовать одну из этих идей?</b>\n\n"
    "На курсе <b>ВАЙБС</b> ты за 4 недели создашь свой проект "
    "— с нуля до работающего продукта. Без кода, без программиста.\n\n"
    "Ученица курса: <i>«То, чему учит Александр — это фантастика "
    "и реальный взрыв мозга от открывающихся возможностей. "
    "Если вы далеки от кода, без наставника шансов освоить даже "
    "вайб-кодинг крайне мало»</i>\n\n"
    "🔥 Старт ближайшего потока — <b>21 февраля</b>. "
    "Всего 20 мест, 5 уже занято."
)


async def send_live_stream_link(chat_id: int, delay_seconds: int = 60) -> None:
    """
    Отправляет ссылку на прямой эфир после задержки.

    Args:
        chat_id: ID чата для отправки сообщения
        delay_seconds: Задержка перед отправкой в секундах (по умолчанию 60)
    """
    await asyncio.sleep(delay_seconds)
    
    message = (
        "Кстати! Если хочешь посмотреть, как создаются такие проекты "
        "в реальном времени — заглядывай на мой прямой эфир.\n\n"
        "Там я показываю весь процесс вайб-кодинга на практике "
        "и отвечаю на вопросы.\n\n"
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
        "Привет! 👋 Я — AI-генератор идей для вайб-кодинга.\n\n"
        "Подберу тебе 3-5 проектов, которые ты сможешь создать сам, "
        "без программиста — за пару вечеров.\n\n"
        "Напиши свою нишу или чем занимаешься — и я подберу идеи под тебя."
    )

    await message.answer(welcome_message, parse_mode="HTML")

    # Логируем приветствие
    log_conversation(
        user_id=message.from_user.id,
        username=message.from_user.username,
        message="/start",
        response=welcome_message
    )


@dp.callback_query(F.data.startswith("idea_"))
async def handle_idea_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Обработчик нажатия кнопок выбора идеи 💡."""
    idea_num = callback.data.split("_")[1]
    await callback.answer()

    user_message = f"Расскажи подробнее об идее {idea_num}"

    # Получаем историю диалога
    data = await state.get_data()
    history = data.get("history", [])

    thinking_msg = await callback.message.answer(
        "Так, тут нужно <i>подумать</i>, дай мне немного времени... 🤔",
        parse_mode="HTML"
    )
    animation_task = asyncio.create_task(animate_thinking(thinking_msg))

    try:
        await callback.message.bot.send_chat_action(
            chat_id=callback.message.chat.id, action="typing"
        )

        response = await llm_client.get_response(user_message, history)
        animation_task.cancel()
        await thinking_msg.delete()

        # Пробуем отправить с HTML, если не получится — без разметки
        try:
            await callback.message.answer(response, parse_mode="HTML")
        except Exception:
            await callback.message.answer(response)

        # Обновляем историю
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": response})
        await state.update_data(history=history[-10:])

        log_conversation(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            message=user_message,
            response=response
        )
    except Exception as e:
        animation_task.cancel()
        await thinking_msg.delete()
        error_logger.error(f"callback: {type(e).__name__}: {e}")
        await callback.message.answer(
            "Произошла ошибка при генерации ответа. Попробуйте ещё раз.",
            parse_mode="HTML"
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

    # Отправляем сообщение "думаю..." и запускаем анимацию
    thinking_msg = await message.answer(
        "Так, тут нужно <i>подумать</i>, дай мне немного времени... 🤔",
        parse_mode="HTML"
    )
    animation_task = asyncio.create_task(animate_thinking(thinking_msg))

    try:
        # Отправляем индикатор набора текста
        await message.bot.send_chat_action(
            chat_id=message.chat.id,
            action="typing"
        )

        # Получаем ответ от LLM
        response = await llm_client.get_response(user_message, history)

        # Останавливаем анимацию и удаляем сообщение "думаю..."
        animation_task.cancel()
        await thinking_msg.delete()

        # Проверяем, есть ли в ответе идеи (маркер — "Какая идея зацепила")
        if "Какая идея зацепила" in response:
            # 1. Картинка
            photo_path = os.path.join(os.path.dirname(__file__), "vibes_image.jpg")
            photo = FSInputFile(photo_path)
            await message.answer_photo(photo=photo)
            # 2. Текст идей с кнопками выбора 💡
            try:
                await message.answer(
                    response, parse_mode="HTML",
                    reply_markup=create_idea_buttons()
                )
            except Exception:
                await message.answer(
                    response, reply_markup=create_idea_buttons()
                )
            # 3. Продающий блок — отдельное сообщение
            await message.answer(
                VIBES_SALES_TEXT, parse_mode="HTML",
                reply_markup=create_vibes_button()
            )
            # 4. Ссылка на стрим через 1 час
            asyncio.create_task(send_live_stream_link(message.chat.id, delay_seconds=3600))
        else:
            try:
                await message.answer(response, parse_mode="HTML")
            except Exception:
                await message.answer(response)

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

    except Exception as e:
        animation_task.cancel()
        await thinking_msg.delete()
        error_logger.error(f"message: {type(e).__name__}: {e}")

        await message.answer(
            "Произошла ошибка при генерации ответа. Попробуйте ещё раз.",
            parse_mode="HTML"
        )

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

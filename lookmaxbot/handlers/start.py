from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from db import get_user
from config import FREE_ANALYSES

router = Router()


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Анализировать фото", callback_data="how_to_analyze")],
        [InlineKeyboardButton(text="📊 Мой профиль", callback_data="my_profile")],
        [InlineKeyboardButton(text="❓ Как это работает", callback_data="how_it_works")],
    ])


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = await get_user(message.from_user.id)
    free_left = max(0, FREE_ANALYSES - user["free_used"])

    await message.answer(
        f"🗿 *LOOKSMAX BOT*\n\n"
        f"Узнай свой честный рейтинг внешности по методологии looksmaxing-коммьюнити.\n\n"
        f"• Оценка по 10 параметрам\n"
        f"• Tier от NPC до Gigachad\n"
        f"• Конкретные советы под твоё лицо\n\n"
        f"🆓 Бесплатных анализов осталось: *{free_left}/{FREE_ANALYSES}*\n\n"
        f"Просто отправь своё фото 👇",
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )


@router.callback_query(lambda c: c.data == "how_to_analyze")
async def how_to_analyze(callback) -> None:
    await callback.message.answer(
        "📸 *Как получить точный результат:*\n\n"
        "✅ Фото при хорошем освещении\n"
        "✅ Смотришь прямо в камеру\n"
        "✅ Нейтральное выражение лица\n"
        "✅ Без фильтров и обработки\n"
        "✅ Волосы убраны с лица\n\n"
        "Просто отправь фото прямо сюда 👇",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "how_it_works")
async def how_it_works(callback) -> None:
    await callback.message.answer(
        "🔬 *Как работает анализ:*\n\n"
        "Бот использует GPT-4o Vision — одну из самых мощных моделей компьютерного зрения.\n\n"
        "Анализируются:\n"
        "• Jawline & Chin\n"
        "• Cheekbones\n"
        "• Eyes & Canthal Tilt\n"
        "• Нос, губы, кожа\n"
        "• Общая гармония черт\n\n"
        "Результат — честный разбор в стиле looksmaxing-коммьюнити.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "my_profile")
async def my_profile(callback) -> None:
    user = await get_user(callback.from_user.id)
    free_left = max(0, FREE_ANALYSES - user["free_used"])

    await callback.message.answer(
        f"📊 *Твой профиль*\n\n"
        f"👤 {callback.from_user.full_name}\n"
        f"🆓 Бесплатных осталось: {free_left}/{FREE_ANALYSES}\n"
        f"💳 Платных анализов: {user['total_paid']}\n"
        f"📈 Всего анализов: {user['free_used'] + user['total_paid']}",
        parse_mode="Markdown",
    )
    await callback.answer()

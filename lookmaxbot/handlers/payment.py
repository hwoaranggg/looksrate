from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    Message,
    LabeledPrice,
    PreCheckoutQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from config import STARS_PER_ANALYSIS, STARS_DETAILED
from db import get_user, increment_paid

router = Router()

# Payload-ы для различения типов покупки
PAYLOAD_ANALYSIS = "analysis_stars"
PAYLOAD_DETAILED = "detailed_stars"


def pay_keyboard(stars: int, payload: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"⭐ Оплатить {stars} Stars",
            pay=True,
        )]
    ])


@router.message(Command("buy"))
async def cmd_buy(message: Message) -> None:
    await message.answer_invoice(
        title="Анализ внешности",
        description=f"Полный looksmax-анализ твоего фото по 10 параметрам",
        payload=PAYLOAD_ANALYSIS,
        currency="XTR",  # Telegram Stars
        prices=[LabeledPrice(label="Анализ", amount=STARS_PER_ANALYSIS)],
        reply_markup=pay_keyboard(STARS_PER_ANALYSIS, PAYLOAD_ANALYSIS),
    )


@router.message(Command("detailed"))
async def cmd_detailed(message: Message) -> None:
    await message.answer_invoice(
        title="Детальный анализ",
        description=(
            "Расширенный разбор: facial thirds, symmetry score, "
            "hunter/prey eyes, потенциал и ROI improvements"
        ),
        payload=PAYLOAD_DETAILED,
        currency="XTR",
        prices=[LabeledPrice(label="Детальный анализ", amount=STARS_DETAILED)],
        reply_markup=pay_keyboard(STARS_DETAILED, PAYLOAD_DETAILED),
    )


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    # Всегда подтверждаем — Stars списываются мгновенно
    await query.answer(ok=True)


@router.message(lambda m: m.successful_payment is not None)
async def successful_payment(message: Message) -> None:
    payload = message.successful_payment.invoice_payload

    if payload == PAYLOAD_ANALYSIS:
        # Помечаем что у пользователя есть оплаченный анализ
        await message.bot.set_my_commands([])  # no-op, флаг через FSM ниже
        await increment_paid(message.from_user.id)
        await message.answer(
            "✅ *Оплата прошла!*\n\n"
            "Теперь отправь своё фото — сделаю полный анализ 📸",
            parse_mode="Markdown",
        )
        # Сохраняем в bot_data что этот user ожидает анализ после оплаты
        pending = message.bot["pending_paid"]
        pending.add(message.from_user.id)

    elif payload == PAYLOAD_DETAILED:
        await increment_paid(message.from_user.id)
        await message.answer(
            "✅ *Оплата прошла!*\n\n"
            "Отправь фото — сделаю детальный разбор с расширенным анализом 🔬",
            parse_mode="Markdown",
        )
        pending_detailed = message.bot["pending_detailed"]
        pending_detailed.add(message.from_user.id)

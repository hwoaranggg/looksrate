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
from db import increment_paid

router = Router()

PAYLOAD_ANALYSIS = "analysis_stars"
PAYLOAD_DETAILED = "detailed_stars"


def pay_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Оплатить", pay=True)]
    ])


@router.message(Command("buy"))
async def cmd_buy(message: Message) -> None:
    await message.answer_invoice(
        title="Анализ внешности",
        description="Полный looksmax-анализ твоего фото по 10 параметрам",
        payload=PAYLOAD_ANALYSIS,
        currency="XTR",
        prices=[LabeledPrice(label="Анализ", amount=STARS_PER_ANALYSIS)],
        reply_markup=pay_keyboard(),
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
        reply_markup=pay_keyboard(),
    )


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(lambda m: m.successful_payment is not None)
async def successful_payment(
    message: Message,
    pending_paid: set,
    pending_detailed: set,
) -> None:
    payload = message.successful_payment.invoice_payload

    if payload == PAYLOAD_ANALYSIS:
        await increment_paid(message.from_user.id)
        pending_paid.add(message.from_user.id)
        await message.answer(
            "✅ *Оплата прошла!*\n\n"
            "Теперь отправь своё фото — сделаю полный анализ 📸",
            parse_mode="Markdown",
        )

    elif payload == PAYLOAD_DETAILED:
        await increment_paid(message.from_user.id)
        pending_detailed.add(message.from_user.id)
        await message.answer(
            "✅ *Оплата прошла!*\n\n"
            "Отправь фото — сделаю детальный разбор 🔬",
            parse_mode="Markdown",
        )

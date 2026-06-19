import sys
from io import BytesIO
from aiogram import Router, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from db import get_user, increment_free
from services.gpt import analyze_face
from services.formatter import format_result
from services.card import generate_card
from config import FREE_ANALYSES, STARS_PER_ANALYSIS

router = Router()


def buy_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"⭐ Купить анализ ({STARS_PER_ANALYSIS} Stars)",
            callback_data="buy_analysis",
        )],
        [InlineKeyboardButton(
            text="🔬 Детальный разбор (10 Stars)",
            callback_data="buy_detailed",
        )],
    ])


@router.message(lambda m: m.photo is not None)
async def handle_photo(message: Message, bot: Bot) -> None:
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Anonymous"
    user = await get_user(user_id)

    free_left = FREE_ANALYSES - user["free_used"]
    pending_paid: set = bot["pending_paid"]
    pending_detailed: set = bot["pending_detailed"]

    is_paid = user_id in pending_paid
    is_detailed = user_id in pending_detailed

    # Проверяем доступ
    if not is_paid and not is_detailed and free_left <= 0:
        await message.answer(
            "🔒 *Бесплатные анализы закончились*\n\n"
            f"Было {FREE_ANALYSES} бесплатных анализа.\n"
            "Продолжить за ⭐ Stars:",
            parse_mode="Markdown",
            reply_markup=buy_keyboard(),
        )
        return

    # Статус — два этапа чтобы пользователь не думал что бот завис
    status = await message.answer(
        "🔍 *Шаг 1/2* — анализирую черты лица...",
        parse_mode="Markdown",
    )

    try:
        # Скачиваем фото максимального размера
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        buf = await bot.download_file(file.file_path)
        image_data = buf.read()

        # Первый + второй проход
        analysis, advice = await analyze_face(image_data, detailed=is_detailed)

        await status.edit_text(
            "⚡ *Шаг 2/2* — составляю персональный roadmap...",
            parse_mode="Markdown",
        )

        msg1, msg2 = format_result(analysis, advice, user_name, detailed=is_detailed)

        # Обновляем счётчики
        if is_paid:
            pending_paid.discard(user_id)
        elif is_detailed:
            pending_detailed.discard(user_id)
        else:
            await increment_free(user_id)

        await status.delete()

        # Генерируем карточку
        try:
            card_bytes = generate_card(analysis, user_name)
            await message.answer_photo(
                photo=BufferedInputFile(card_bytes, filename="looksmax_result.png"),
                caption="🔬 *Твой LOOKSMAX результат* — сохрани и поделись!",
                parse_mode="Markdown",
            )
        except Exception as card_err:
            print(f"[WARN] card generation failed: {card_err}", file=sys.stderr)

        # Два отдельных сообщения — анализ и roadmap
        await message.answer(msg1, parse_mode="Markdown")
        await message.answer(msg2, parse_mode="Markdown")

        # Если исчерпал бесплатные — предлагаем купить
        user_after = await get_user(user_id)
        if (
            not is_paid
            and not is_detailed
            and FREE_ANALYSES - user_after["free_used"] == 0
        ):
            await message.answer(
                "⚠️ *Это был последний бесплатный анализ.*\n"
                "Следующий — за Stars:",
                parse_mode="Markdown",
                reply_markup=buy_keyboard(),
            )

    except Exception as e:
        await status.delete()
        await message.answer(
            "❌ Не удалось проанализировать фото.\n"
            "Попробуй ещё раз — убедись что на фото чётко видно лицо."
        )
        print(f"[ERROR] analyze user={user_id}: {e}", file=sys.stderr)


@router.callback_query(lambda c: c.data == "buy_analysis")
async def cb_buy_analysis(callback) -> None:
    from handlers.payment import cmd_buy
    await cmd_buy(callback.message)
    await callback.answer()


@router.callback_query(lambda c: c.data == "buy_detailed")
async def cb_buy_detailed(callback) -> None:
    from handlers.payment import cmd_detailed
    await cmd_detailed(callback.message)
    await callback.answer()

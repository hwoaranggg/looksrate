import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from db import init_db
from handlers import start, analyze, payment


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )

    # In-memory sets для отслеживания оплаченных сессий
    # (при рестарте бота сбрасываются — пользователь просто нажмёт /buy снова)
    bot["pending_paid"] = set()
    bot["pending_detailed"] = set()

    dp = Dispatcher()

    # Роутеры — порядок важен: payment раньше analyze
    dp.include_router(start.router)
    dp.include_router(payment.router)
    dp.include_router(analyze.router)

    await init_db()
    logging.info("DB initialized")

    logging.info("Bot started")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())

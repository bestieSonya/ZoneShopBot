#простой пример 
import asyncio
import logging
import os
from typing import Final

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    AIORateLimiter,   # убрать, если не установлен extras [rate-limiter]
    JobQueue          # убрать, если не установлен extras [job-queue]
)

BOT_TOKEN: Final[str] = os.getenv("TOKEN", "").strip()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Бот запущен и готов к работе ✅")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.text:
        await update.message.reply_text(f"Echo: {update.message.text}")

def build_app() -> Application:
    if not BOT_TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN в окружении")

    # Если extras [rate-limiter] не установлен, удалите rate_limiter=
    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .rate_limiter(AIORateLimiter())  # требует extras [rate-limiter]
        .parse_mode(ParseMode.HTML)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Пример инициализации джобов (требует extras [job-queue])
    jq: JobQueue = app.job_queue  # доступно по умолчанию, но APScheduler нужен для продвинутых кейсов
    # jq.run_repeating(callback=..., interval=60, name="heartbeat")

    return app

async def amain() -> None:
    app = build_app()
    await app.initialize()
    try:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        await app.updater.idle()
    finally:
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(amain())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Остановка бота")

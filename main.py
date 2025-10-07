import logging
import os
import sys
import pathlib
from typing import Final

sys.path.append(str(pathlib.Path(__file__).resolve().parent))

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    AIORateLimiter,
    Defaults
)

try:
    from middlewaresBeta.auth import handlers, UD_PASSED
    AUTH_ENABLED = True
except ImportError:
    AUTH_ENABLED = False
    UD_PASSED = "auth_passed"

load_dotenv()

BOT_TOKEN: Final[str] = os.getenv("TOKEN", "").strip()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(f"Привет, {user.first_name}! Бот запущен.")

async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if AUTH_ENABLED and not context.user_data.get(UD_PASSED):
        return
    
    if update.message and update.message.text:
        await update.message.reply_text(f"Echo: {update.message.text}")

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if AUTH_ENABLED and not context.user_data.get(UD_PASSED):
        return
    
    help_text = (
        "<b>Доступные команды:</b>\n"
        "/help - справка\n"
        "/start - перезапуск\n\n"
        "Отправьте любое сообщение для эхо."
    )
    await update.message.reply_text(help_text)

def create_application() -> Application:
    defaults = Defaults(parse_mode=ParseMode.HTML)
    
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .rate_limiter(AIORateLimiter())
        .defaults(defaults)
        .build()
    )
    
    if AUTH_ENABLED:
        conv_handler, gate_handler = handlers()
        app.add_handler(conv_handler)
        app.add_handler(gate_handler)
    else:
        app.add_handler(CommandHandler("start", start_handler))
    
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler))
    
    return app

def main() -> None:
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment")
        return
    
    app = create_application()
    logger.info("Bot starting...")
    
    try:
        app.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")

if __name__ == "__main__":
    main()
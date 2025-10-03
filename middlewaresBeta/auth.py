import time
import secrets
from io import BytesIO
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)


AWAIT_CODE = 1


UD_CODE = "auth_code"
UD_DEADLINE = "auth_deadline"
UD_PASSED = "auth_passed"

CAPTCHA_TTL = 90  
CODE_LEN = 5

def _gen_code(n: int = CODE_LEN) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(n))

def _gen_image(text: str) -> BytesIO:
    img = Image.new("RGB", (220, 80), color=(240, 240, 240))
    d = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except Exception:
        font = ImageFont.load_default()
   #НАСТРОЙКА
    w, h = d.textlength(text, font=font), 36
    x = (220 - w) / 2
    y = (80 - h) / 2
    d.text((x, y), text, fill=(20, 20, 20), font=font)
    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio

async def start_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
 #ГЕН.КАПЧИ
    code = _gen_code()
    context.user_data[UD_CODE] = code
    context.user_data[UD_DEADLINE] = time.time() + CAPTCHA_TTL
    context.user_data[UD_PASSED] = False

    img = _gen_image(code)
    if update.message:
        await update.message.reply_photo(
            photo=img,
            caption=f"Введите код с изображения. У вас {CAPTCHA_TTL} сек."
        )
    return AWAIT_CODE

async def on_captcha_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    code = context.user_data.get(UD_CODE)
    deadline = context.user_data.get(UD_DEADLINE, 0)
    if not code or time.time() > deadline:
        context.user_data.pop(UD_CODE, None)
        context.user_data.pop(UD_DEADLINE, None)
        await update.message.reply_text("Время вышло. Отправьте /start для новой капчи.")
        return ConversationHandler.END

    user_text = (update.message.text or "").strip().upper()
    if user_text == code:
        context.user_data[UD_PASSED] = True
        context.user_data.pop(UD_CODE, None)
        context.user_data.pop(UD_DEADLINE, None)
        await update.message.reply_text("Капча пройдена. Добро пожаловать в бота.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Неверно. Попробуйте ещё раз или отправьте /start, чтобы получить новую капчу.")
        return AWAIT_CODE

async def gatekeeper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get(UD_PASSED):
        return  
    if update.message and update.message.text and update.message.text.startswith("/start"):
        return  
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Сначала пройдите капчу: /start")

def handlers() -> Tuple[ConversationHandler, MessageHandler]:
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start_captcha)],
        states={
            AWAIT_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, on_captcha_reply)],
        },
        fallbacks=[],
        conversation_timeout=CAPTCHA_TTL + 30,
    )
    gate = MessageHandler(filters.ALL, gatekeeper)
    return conv, gate

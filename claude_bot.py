import anthropic
import base64
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.constants import ChatAction

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
history = {}
max_history_length = 20

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user_id = update.message.from_user.id
    user_text = update.message.text

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    if user_id not in history:
        history[user_id] = []

    history[user_id].append({"role": "user", "content": user_text})

    if len(history[user_id]) > max_history_length:
        history[user_id] = history[user_id][-max_history_length:]

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=history[user_id]
    )

    reply = response.content[0].text
    history[user_id].append({"role": "assistant", "content": reply})

    await update.message.reply_text(reply)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = update.message.from_user.id
    caption = update.message.caption or "Что на этом изображении?"

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    if user_id not in history:
        history[user_id] = []

    history[user_id].append({
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_base64
                }
            },
            {"type": "text", "text": caption}
        ]
    })

    if len(history[user_id]) > max_history_length:
        history[user_id] = history[user_id][-max_history_length:]

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=history[user_id]
    )

    reply = response.content[0].text
    history[user_id].append({"role": "assistant", "content": reply})

    await update.message.reply_text(reply)

async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    command = update.message.text

    if command == "/start":
        history[user_id] = []
        await update.message.reply_text("Введите ваш запрос.")
    elif command == "/clear":
        history[user_id] = []
        await update.message.reply_text("История очищена.")
    elif command == "/help":
        await update.message.reply_text("You can ask me anything! Just type your question and I'll do my best to assist you.")

PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler(["start", "clear", "help"], command_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

print("Clavdiy is now online")
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    webhook_url=f"https://{WEBHOOK_URL}"
)

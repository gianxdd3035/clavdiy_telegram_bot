import anthropic
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.constants import ChatAction, ParseMode

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
history = {}
max_history_length = 20

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
        )

    if user_id not in history:
        history[user_id] = []

    history[user_id].append({"role": "user", "content": user_text})

async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    history[update.message.from_user.id] = []
    command = update.message.text
    if command == "/start":
        await update.message.reply_text("Введите ваш запрос.")
    elif command == "/clear":
        await update.message.reply_text("История очищена.")
    elif command == "/help":
        await update.message.reply_text("You can ask me anything! Just type your question and I'll do my best to assist you.")

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

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler(["start", "clear", "help"], command_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()

import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = (os.environ.get("BOT_TOKEN") or "").strip()

print("TOKEN_LENGTH=", len(TOKEN), flush=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("handler start called", flush=True)
    await update.message.reply_text(f"OK. your id = {update.effective_chat.id}")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("handler ping called", flush=True)
    await update.message.reply_text("PING ZENDE ✅")

def main():
    print("main() called", flush=True)

    if not TOKEN:
        print("NO TOKEN", flush=True)
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))

    print("before run_polling", flush=True)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from config import Config
import ai_groq

# Logs básicos
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! 👋 Soy VentasBot en Telegram. ¿Qué ropa buscas?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    text = update.message.text
    
    # Indicador "escribiendo..."
    await context.bot.send_chat_action(chat_id=user_id, action="typing")
    
    # Procesar con Groq
    response = ai_groq.get_groq_response(user_id, text)
    await update.message.reply_text(response)

if __name__ == '__main__':
    if not Config.TELEGRAM_TOKEN or "PON_AQUI" in Config.TELEGRAM_TOKEN:
        print("❌ ERROR: Rellena el token de Telegram en el archivo .env")
    else:
        print("🚀 Bot de Telegram INICIADO...")
        app = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler('start', start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        app.run_polling()
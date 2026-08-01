# bot/bot.py

import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from ai_model import generate_signal as ai_generate_signal
from screenshot_analyzer import analyze_screenshot
import logging

logging.basicConfig(level=logging.INFO)

with open('config.json', 'r') as f:
    config = json.load(f)

TOKEN = config['telegram_token']
CHAT_ID = None

# ========== КОМАНДЫ ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    CHAT_ID = update.effective_chat.id
    await update.message.reply_text(
        "🧠 *AI SIGNAL BOT XAUUSD*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Модель: LSTM + Attention (64 нейрона)\n"
        "Признаки: 10 (RSI, MACD, ATR, Stochastic, BB, ...)\n\n"
        "🔹 /signal — AI-сигнал (рынок)\n"
        "🔹 /status — статус модели\n"
        "🔹 /start — меню\n"
        "🖼 Отправь скриншот графика — анализ по картинке",
        parse_mode="Markdown"
    )

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = ai_generate_signal()
    emoji = "🟢" if data['signal'] == 'BUY' else "🔴" if data['signal'] == 'SELL' else "⏸"
    conf_emoji = "🔥" if data['confidence'] == 'HIGH' else "⚡" if data['confidence'] == 'MEDIUM' else "💤"
    
    msg = (
        f"{emoji} *AI СИГНАЛ XAUUSD* {conf_emoji}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Цена: `${data['price']}`\n"
        f"📈 Решение: *{data['signal']}*\n"
        f"🎯 Уверенность: {data['confidence']}\n"
        f"🤖 AI прогноз: `{data['prediction']}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 {data['reason']}\n"
        f"🕐 {data['time']}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 *AI Модель активна*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Архитектура: LSTM + Attention\n"
        "Размер LSTM: 64 нейрона\n"
        "Глубина истории: 100 баров\n"
        "Количество признаков: 10\n"
        "Символ: XAUUSD\n"
        "Интервал: 5 минут\n"
        "🖼 Анализ скриншотов: включён",
        parse_mode="Markdown"
    )

# ========== ОБРАБОТКА СКРИНШОТОВ ==========

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает скриншот, отправленный пользователем"""
    await update.message.reply_text("🔄 Анализирую скриншот... Подождите.")
    
    # Получаем файл
    photo_file = await update.message.photo[-1].get_file()
    image_bytes = await photo_file.download_as_bytearray()
    
    # Анализ
    result = analyze_screenshot(bytes(image_bytes))
    
    if result['signal'] == 'HOLD' and result['price'] == 0:
        await update.message.reply_text(
            "❌ *Не удалось проанализировать скриншот*\n\n"
            "📌 Отправь чёткий скриншот графика XAUUSD с индикаторами (RSI, MACD).\n"
            "Я распознаю цены, уровни и индикаторы.",
            parse_mode="Markdown"
        )
        return
    
    emoji = "🟢" if result['signal'] == 'BUY' else "🔴" if result['signal'] == 'SELL' else "⏸"
    conf_emoji = "🔥" if result['confidence'] == 'HIGH' else "⚡" if result['confidence'] == 'MEDIUM' else "💤"
    
    msg = (
        f"{emoji} *СИГНАЛ СО СКРИНШОТА* {conf_emoji}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Цена: `${result['price']}`\n"
        f"📈 Решение: *{result['signal']}*\n"
        f"🎯 Уверенность: {result['confidence']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡 Поддержка: `{result['support']}`\n"
        f"🗻 Сопротивление: `{result['resistance']}`\n"
        f"📊 RSI: `{result['rsi']}`\n"
        f"📉 MACD: `{result['macd']}`\n"
        f"📊 Счёт: `{result['score']}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 {result['reason']}\n"
        f"🕐 {result['time']}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# ========== АВТО-РАССЫЛКА ==========

async def auto_signal(context: ContextTypes.DEFAULT_TYPE):
    if not CHAT_ID:
        return
    data = ai_generate_signal()
    emoji = "🟢" if data['signal'] == 'BUY' else "🔴" if data['signal'] == 'SELL' else "⏸"
    conf_emoji = "🔥" if data['confidence'] == 'HIGH' else "⚡" if data['confidence'] == 'MEDIUM' else "💤"
    
    msg = (
        f"{emoji} *АВТО-СИГНАЛ XAUUSD* {conf_emoji}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Цена: `${data['price']}`\n"
        f"📈 Решение: *{data['signal']}*\n"
        f"🎯 Уверенность: {data['confidence']}\n"
        f"🤖 AI прогноз: `{data['prediction']}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 {data['reason']}\n"
        f"🕐 {data['time']}"
    )
    await context.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

# ========== ЗАПУСК ==========

def main():
    app = Application.builder().token(TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("status", status))
    
    # Обработка фото
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Авто-рассылка (каждые 5 минут)
    job_queue = app.job_queue
    job_queue.run_repeating(auto_signal, interval=300, first=10)
    
    print("✅ AI бот запущен (с анализом скриншотов)")
    app.run_polling()

if __name__ == "__main__":
    main()

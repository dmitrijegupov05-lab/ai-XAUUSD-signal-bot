import json
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from ai_model import generate_signal as ai_generate_signal
from screenshot_analyzer import analyze_screenshot

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== ПОЛУЧЕНИЕ ТОКЕНА ==========
TOKEN = os.environ.get('TELEGRAM_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_TOKEN не найден в переменных окружения!")
    raise ValueError("TELEGRAM_TOKEN not set in environment variables")

logger.info("✅ Токен загружен успешно")

# ========== ЗАГРУЗКА КОНФИГА ==========
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    logger.info("✅ Конфиг загружен")
except FileNotFoundError:
    logger.error("Файл config.json не найден!")
    config = {"symbol": "XAUUSD", "update_interval_seconds": 300}

CHAT_ID = None

# ========== КОМАНДЫ ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    CHAT_ID = update.effective_chat.id
    logger.info(f"Пользователь {CHAT_ID} запустил бота")
    
    await update.message.reply_text(
        "🧠 *AI SIGNAL BOT XAUUSD*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Модель: LSTM + Attention (64 нейрона)\n"
        "Признаки: 10 (RSI, MACD, ATR, Stochastic, BB, ...)\n\n"
        "🔹 /signal — получить AI-сигнал сейчас\n"
        "🔹 /status — статус модели\n"
        "🔹 /start — это меню\n"
        "🖼 Отправь скриншот графика — анализ по картинке\n\n"
        "📡 Бот будет присылать сигналы автоматически каждые 5 минут",
        parse_mode="Markdown"
    )

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Запрос сигнала от пользователя")
    data = ai_generate_signal()
    
    emoji = "🟢" if data['signal'] == 'BUY' else "🔴" if data['signal'] == 'SELL' else "⏸"
    conf_emoji = "🔥" if data['confidence'] == 'HIGH' else "⚡" if data['confidence'] == 'MEDIUM' else "💤"
    
    await update.message.reply_text(
        f"{emoji} *AI СИГНАЛ XAUUSD* {conf_emoji}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Цена: `${data['price']}`\n"
        f"📈 Решение: *{data['signal']}*\n"
        f"🎯 Уверенность: {data['confidence']}\n"
        f"🤖 AI прогноз: `{data['prediction']}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 {data['reason']}\n"
        f"🕐 {data['time']}",
        parse_mode="Markdown"
    )

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
        "🖼 Анализ скриншотов: включён\n"
        "📡 Авто-рассылка: активна",
        parse_mode="Markdown"
    )

# ========== ОБРАБОТКА СКРИНШОТОВ ==========

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Анализирую скриншот... Подождите.")
    
    try:
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
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
        
        await update.message.reply_text(
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
            f"🕐 {result['time']}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка при анализе скриншота: {e}")
        await update.message.reply_text(
            "❌ *Ошибка при анализе скриншота*\n\n"
            f"Техническая ошибка: `{str(e)}`",
            parse_mode="Markdown"
        )

# ========== АВТОМАТИЧЕСКАЯ РАССЫЛКА ==========

async def auto_signal(context: ContextTypes.DEFAULT_TYPE):
    if not CHAT_ID:
        logger.warning("CHAT_ID не установлен, пропускаем авто-сигнал")
        return
    
    try:
        data = ai_generate_signal()
        emoji = "🟢" if data['signal'] == 'BUY' else "🔴" if data['signal'] == 'SELL' else "⏸"
        conf_emoji = "🔥" if data['confidence'] == 'HIGH' else "⚡" if data['confidence'] == 'MEDIUM' else "💤"
        
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=(
                f"{emoji} *АВТО-СИГНАЛ XAUUSD* {conf_emoji}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 Цена: `${data['price']}`\n"
                f"📈 Решение: *{data['signal']}*\n"
                f"🎯 Уверенность: {data['confidence']}\n"
                f"🤖 AI прогноз: `{data['prediction']}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📝 {data['reason']}\n"
                f"🕐 {data['time']}"
            ),
            parse_mode="Markdown"
        )
        logger.info("Авто-сигнал отправлен")
    except Exception as e:
        logger.error(f"Ошибка при отправке авто-сигнала: {e}")

# ========== ЗАПУСК ==========

def main():
    logger.info("🚀 Запуск AI Signal Bot XAUUSD")
    
    app = Application.builder().token(TOKEN).build()
    
    # Регистрация команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("status", status))
    
    # Регистрация обработчика фото
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Автоматическая рассылка каждые 5 минут
    job_queue = app.job_queue
    job_queue.run_repeating(auto_signal, interval=300, first=10)
    
    logger.info("✅ Бот готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()

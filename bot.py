import time
import requests
import logging
from datetime import datetime, timedelta
from binance.client import Client
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# ====== НАЛАШТУВАННЯ ======
BINANCE_API_KEY = "QmlOP0W9qiIqGcNrYuheViqC9Jekp6X3bIMghn6XtbLOYTxKor3J60u5nhzFivnd"
BINANCE_API_SECRET = "k2oIUMOaMFVQBy8Di3rTW1hGQGDGyJMMRTV3D3nyydd9DhmwitbleeMFR7bJkCMq"
TELEGRAM_TOKEN = "8129732857:AAGS1yAqHmEaSS2LiiEsQvKM-Ye86p2oW_I"
TELEGRAM_CHAT_ID = "6913973601"  # ID чату куди слати сигнали (можна дізнатися через @userinfobot)
DEFAULT_PERCENT_CHANGE = 5  # За замовчуванням 5%
DEFAULT_TIMEFRAME = 10  # За замовчуванням 10 хвилин

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
last_signals = {}  # Лог сигналів {symbol: count}
user_settings = {}  # Налаштування для користувачів {user_id: {'percent': X, 'time': Y}}

# ====== ЛОГІКА АНАЛІЗУ РИНКУ ======
def get_binance_prices():
    """Отримує ціни монет з Binance."""
    tickers = client.get_ticker()
    return {t["symbol"]: float(t["lastPrice"]) for t in tickers if t["symbol"].endswith("USDT")}

def check_market():
    """Перевіряє ринок та надсилає сигнал у ТГ, якщо є різке зростання."""
    global last_signals
    current_time = datetime.now()
    
    prices_now = get_binance_prices()
    time.sleep(60)  # Чекаємо одну хвилину
    prices_later = get_binance_prices()

    signals_today = sum(last_signals.values())  # Сигналів за добу

    for symbol, old_price in prices_now.items():
        new_price = prices_later.get(symbol)
        if not new_price:
            continue
        
        percent_change = ((new_price - old_price) / old_price) * 100
        
        # Користувацькі або дефолтні налаштування
        percent_threshold = user_settings.get(TELEGRAM_CHAT_ID, {}).get("percent", DEFAULT_PERCENT_CHANGE)

        if percent_change >= percent_threshold:
            last_signals[symbol] = last_signals.get(symbol, 0) + 1
            signals_today += 1
            
            message = f"🚀 *Ріст ціни!*\nМонета: {symbol}\n📈 Зміна: +{percent_change:.2f}%\n⏳ Інтервал: 1 хв\n🔔 Сигналів за добу: {signals_today}"
            send_telegram_alert(message)

    # Очищення історії сигналів щодня опівночі
    if current_time.hour == 0 and current_time.minute == 0:
        last_signals.clear()

def send_telegram_alert(message):
    """Відправляє повідомлення в Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=data)

# ====== КЕРУВАННЯ ЧЕРЕЗ TELEGRAM ======
def start(update: Update, context: CallbackContext):
    """Обробляє команду /start."""
    update.message.reply_text("Привіт! Я моніторю ринок Binance. Використовуй команди:\n/set_percent X% – змінити поріг\n/set_time Xхв – змінити інтервал")

def set_percent(update: Update, context: CallbackContext):
    """Команда для зміни порогу відсотка."""
    user_id = update.message.chat_id
    try:
        percent = int(context.args[0].replace("%", ""))
        if 1 <= percent <= 100:
            user_settings[user_id] = user_settings.get(user_id, {})
            user_settings[user_id]["percent"] = percent
            update.message.reply_text(f"✅ Поріг змінено на {percent}%")
        else:
            update.message.reply_text("⚠️ Введи значення від 1 до 100")
    except (IndexError, ValueError):
        update.message.reply_text("⚠️ Використання: /set_percent 5%")

def set_time(update: Update, context: CallbackContext):
    """Команда для зміни інтервалу перевірки."""
    user_id = update.message.chat_id
    try:
        minutes = int(context.args[0].replace("хв", ""))
        if 1 <= minutes <= 30:
            user_settings[user_id] = user_settings.get(user_id, {})
            user_settings[user_id]["time"] = minutes
            update.message.reply_text(f"✅ Інтервал змінено на {minutes} хв")
        else:
            update.message.reply_text("⚠️ Введи значення від 1 до 30 хвилин")
    except (IndexError, ValueError):
        update.message.reply_text("⚠️ Використання: /set_time 10хв")

# ====== ЗАПУСК БОТА ======
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("set_percent", set_percent))
    dp.add_handler(CommandHandler("set_time", set_time))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, start))  # Для інших текстів

    updater.start_polling()

    while True:
        check_market()
        time.sleep(60)  # Кожну хвилину перевіряємо

if __name__ == "__main__":
    main()

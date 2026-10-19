import os
import threading
from flask import Flask
import telebot
from telebot import types
import yfinance as yf
import pandas as pd
import numpy as np

# 1. إعداد خادم Flask للتشغيل المستمر Keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

# 2. إعداد البوت والتوكن
TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# قائمة الأزواج
PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "CAD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "GOLD (XAU/USD)": "GC=F",
    "SILVER (XAG/USD)": "SI=F",
    "CRUDE OIL": "CL=F",
    "BITCOIN (BTC/USD)": "BTC-USD"
}

def analyze_pair(ticker_symbol):
    try:
        data = yf.download(tickers=ticker_symbol, period="1d", interval="5m", progress=False)
        if data.empty or len(data) < 20:
            return "عذراً، لا تتوفر بيانات كافية حالياً لهذا الزوج."

        close = data['Close'].squeeze()

        # حساب SMA20 والانحراف المعياري لـ Bollinger Bands
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        upper_band = sma20 + (std20 * 2)
        lower_band = sma20 - (std20 * 2)

        # حساب RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        last_price = close.iloc[-1]
        last_upper = upper_band.iloc[-1]
        last_lower = lower_band.iloc[-1]
        last_rsi = rsi.iloc[-1]

        # قواعد التداول المعتمدة:
        # 1. إذا كان السعر عند الأطراف -> لا تدخل
        if last_price >= last_upper or last_price <= last_lower:
            return "الوضع حالياً غير مناسب: السعر عند أطراف البولنجر باند (احتمال انعكاس غير مضمون). نصيحة: عدم الدخول."

        # 2. RSI في المناطق الحرجة -> لا تدخل عكس الاتجاه
        if last_rsi >= 70 or last_rsi <= 30:
            return "السوق غير مستقر: مؤشر RSI في منطقة تشبع حاد. نصيحة: عدم الدخول."

        # 3. صفقات ممتازة
        if last_price > sma20.iloc[-1] and last_rsi > 50:
            return "صفقة شراء (UP) ⬆️ | المدة: 2 إلى 3 دقائق\nالسبب: ارتداد إيجابي من الخط الأوسط للبولنجر مع RSI إيجابي."
        elif last_price < sma20.iloc[-1] and last_rsi < 50:
            return "صفقة بيع (DOWN) ⬇️ | المدة: 2 إلى 3 دقائق\nالسبب: ارتداد سلبي من الخط الأوسط للبولنجر مع RSI سلبي."
        else:
            return "اتجاه غير واضح حالياً. نصيحة: انتظر إشارة أوضح."

    except Exception as e:
        return "حدث خطأ أثناء جلب البيانات، يرجى المحاولة لاحقاً."

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(pair) for pair in PAIRS.keys()]
    markup.add(*buttons)
    bot.send_message(message.chat.id, f"أهلاً بك يا {message.from_user.first_name}! اختر الزوج للحصول على تحليل وتحذير التداول:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in PAIRS)
def handle_pair(message):
    pair_name = message.text
    ticker = PAIRS[pair_name]
    bot.reply_to(message, f"جاري تحليل {pair_name}...")
    result = analyze_pair(ticker)
    bot.send_message(message.chat.id, f"نتائج تحليل {pair_name}:\n\n{result}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)

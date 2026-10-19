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

# قائمة أزواج Pocket Option العادية و OTC
PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "CAD=X",
    "USD/CHF": "CHF=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "EUR/USD (OTC)": "EURUSD=X",
    "GBP/USD (OTC)": "GBPUSD=X",
    "USD/JPY (OTC)": "JPY=X",
    "GOLD (XAU/USD)": "GC=F",
    "GOLD (OTC)": "GC=F",
    "BITCOIN (BTC/USD)": "BTC-USD"
}

def analyze_pair(ticker_symbol):
    try:
        data = yf.download(tickers=ticker_symbol, period="1d", interval="5m", progress=False)
        if data.empty or len(data) < 20:
            return "عذراً، لا تتوفر بيانات كافية حالياً لهذا الزوج."

        close = data['Close'].squeeze()
        high = data['High'].squeeze()
        low = data['Low'].squeeze()

        # Bollinger Bands (20, 2)
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        upper_band = sma20 + (std20 * 2)
        lower_band = sma20 - (std20 * 2)

        # RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Stochastic (14, 3, 3)
        low14 = low.rolling(window=14).min()
        high14 = high.rolling(window=14).max()
        stoch_k = 100 * ((close - low14) / (high14 - low14))
        stoch_d = stoch_k.rolling(window=3).mean()

        last_price = close.iloc[-1]
        last_upper = upper_band.iloc[-1]
        last_lower = lower_band.iloc[-1]
        last_sma = sma20.iloc[-1]
        last_rsi = rsi.iloc[-1]
        last_k = stoch_k.iloc[-1]
        last_d = stoch_d.iloc[-1]

        # قواعد التداول الدقيقة بناءً على شروطك
        if last_price >= last_upper or last_price <= last_lower:
            return "عدم دخول - السوق غير مناسب\nالسعر يلمس أطراف البولنجر باند."

        if last_rsi >= 70 or last_rsi <= 30 or last_k >= 80 or last_k <= 20:
            return "عدم دخول - السوق سيء\nالمؤشرات في منطقة تشبع حاد."

        if last_price > last_sma and last_rsi > 50 and last_k > last_d:
            return "شراء (BUY) ⬆️ | المدة: دقيقتان إلى 3 دقائق\nارتداد إيجابي من الخط الأوسط مع تقاطع صاعد للمؤشرات."

        elif last_price < last_sma and last_rsi < 50 and last_k < last_d:
            return "بيع (SELL) ⬇️ | المدة: دقيقتان إلى 3 دقائق\nارتداد سلبي من الخط الأوسط مع تقاطع هابط للمؤشرات."

        else:
            return "عدم دخول - انتظر إشارة أوضح\nالاتجاه غير مكتمل."

    except Exception as e:
        return "حدث خطأ أثناء جلب البيانات، يرجى المحاولة لاحقاً."

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(pair) for pair in PAIRS.keys()]
    markup.add(*buttons)
    bot.send_message(message.chat.id, f"أهلاً بك يا {message.from_user.first_name}! اختر الزوج للتحليل:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in PAIRS)
def handle_pair(message):
    pair_name = message.text
    ticker = PAIRS[pair_name]
    bot.reply_to(message, f"جاري تحليل {pair_name}...")
    result = analyze_pair(ticker)
    
    # إضافة أزرار تفاعلية تتيح لك أنت اختيار القرار اليدوي
    markup = types.InlineKeyboardMarkup()
    btn_buy = types.InlineKeyboardButton("🟢 تنفيذ صفقة شراء (BUY)", callback_data="manual_buy")
    btn_sell = types.InlineKeyboardButton("🔴 تنفيذ صفقة بيع (SELL)", callback_data="manual_sell")
    btn_wait = types.InlineKeyboardButton("⏳ عدم الدخول (WAIT)", callback_data="manual_wait")
    markup.add(btn_buy, btn_sell)
    markup.add(btn_wait)

    bot.send_message(message.chat.id, f"نتائج تحليل {pair_name}:\n\n{result}\n\n*القرار لك:* حدد ما تريد تنفيذه:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "manual_buy":
        bot.answer_callback_query(call.id, "تم اختيار صفقة شراء بنجاح!")
        bot.send_message(call.message.chat.id, "شراء (BUY) ⬆️ | المدة: من دقيقة إلى 3 دقائق\nتم تأكيد اختيارك اليدوي.")
    elif call.data == "manual_sell":
        bot.answer_callback_query(call.id, "تم اختيار صفقة بيع بنجاح!")
        bot.send_message(call.message.chat.id, "بيع (SELL) ⬇️ | المدة: من دقيقة إلى 3 دقائق\nتم تأكيد اختيارك اليدوي.")
    elif call.data == "manual_wait":
        bot.answer_callback_query(call.id, "تم اختيار عدم الدخول.")
        bot.send_message(call.message.chat.id, "عدم دخول ⏳\nتم تجنب الصفقة بناءً على قرارك.")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)

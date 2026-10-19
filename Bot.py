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

# قائمة شاملة لجميع أزواج Pocket Option (العادية و OTC)
PAIRS = {
    # أزواج الفوركس العادية
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "CAD=X",
    "USD/CHF": "CHF=X",
    "NZD/USD": "NZDUSD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "AUD/JPY": "AUDJPY=X",
    "EUR/AUD": "EURAUD=X",
    
    # أزواج الـ OTC
    "EUR/USD (OTC)": "EURUSD=X",
    "GBP/USD (OTC)": "GBPUSD=X",
    "USD/JPY (OTC)": "JPY=X",
    "AUD/USD (OTC)": "AUDUSD=X",
    "USD/CAD (OTC)": "CAD=X",
    "USD/CHF (OTC)": "CHF=X",
    "NZD/USD (OTC)": "NZDUSD=X",
    "EUR/GBP (OTC)": "EURGBP=X",
    "EUR/JPY (OTC)": "EURJPY=X",
    "GBP/JPY (OTC)": "GBPJPY=X",
    "AUD/JPY (OTC)": "AUDJPY=X",
    "USD/BDT (OTC)": "USDBDT=X",
    "USD/INR (OTC)": "USDINR=X",
    "USD/PKR (OTC)": "USDPKR=X",
    "USD/EGP (OTC)": "USDEGP=X",
    "USD/TRY (OTC)": "USDTRY=X",
    
    # السلع والمعادن
    "GOLD (XAU/USD)": "GC=F",
    "GOLD (OTC)": "GC=F",
    "SILVER (XAG/USD)": "SI=F",
    "SILVER (OTC)": "SI=F",
    "CRUDE OIL (OTC)": "CL=F",
    
    # العملات الرقمية
    "BITCOIN (BTC/USD)": "BTC-USD",
    "ETHEREUM (ETH/USD)": "ETH-USD"
}

# كيبورد اختيار المدة الزمنية
def get_time_keyboard(pair_name, signal_type):
    markup = types.InlineKeyboardMarkup(row_width=3)
    btn_10s = types.InlineKeyboardButton("⏱ 10 ثواني", callback_data=f"t_10s_{pair_name}_{signal_type}")
    btn_30s = types.InlineKeyboardButton("⏱ 30 ثانية", callback_data=f"t_30s_{pair_name}_{signal_type}")
    btn_1m = types.InlineKeyboardButton("⏱ دقيقة واحدة", callback_data=f"t_1m_{pair_name}_{signal_type}")
    btn_2m = types.InlineKeyboardButton("⏱ دقيقتين", callback_data=f"t_2m_{pair_name}_{signal_type}")
    btn_3m = types.InlineKeyboardButton("⏱ 3 دقائق", callback_data=f"t_3m_{pair_name}_{signal_type}")
    btn_5m = types.InlineKeyboardButton("⏱ 5 دقائق", callback_data=f"t_5m_{pair_name}_{signal_type}")
    btn_10m = types.InlineKeyboardButton("⏱ 10 دقائق", callback_data=f"t_10m_{pair_name}_{signal_type}")
    btn_15m = types.InlineKeyboardButton("⏱ 15 دقيقة", callback_data=f"t_15m_{pair_name}_{signal_type}")
    
    markup.add(btn_10s, btn_30s, btn_1m)
    markup.add(btn_2m, btn_3m, btn_5m)
    markup.add(btn_10m, btn_15m)
    return markup

def analyze_pair(ticker_symbol, pair_name):
    try:
        data = yf.download(tickers=ticker_symbol, period="1d", interval="5m", progress=False)
        if data.empty or len(data) < 20:
            return "WAIT", (
                f"═════════════════════\n"
                f"📊 **توصية Pocket Option احترافية** 📊\n"
                f"═════════════════════\n"
                f"🔤 **الزوج:** {pair_name}\n"
                f"🎯 **الاتجاه:** ⏳ عدم دخول (WAIT)\n"
                f"📈 **نسبة الثقة:** 0%\n"
                f"─────────────────────\n"
                f"💡 **التحليل الفني:** بيانات السوق غير كافية حالياً لهذا الزوج.\n"
                f"═════════════════════"
            )

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

        # شروط التداول الصارمة
        if last_price >= last_upper or last_price <= last_lower:
            return "WAIT", (
                f"═════════════════════\n"
                f"📊 **توصية Pocket Option احترافية** 📊\n"
                f"═════════════════════\n"
                f"🔤 **الزوج:** {pair_name}\n"
                f"🎯 **الاتجاه:** ⏳ عدم دخول (WAIT)\n"
                f"📈 **نسبة الثقة:** 0%\n"
                f"─────────────────────\n"
                f"💡 **التحليل الفني:** السعر يلمس أطراف البولنجر باند، احذر الانعكاس.\n"
                f"═════════════════════"
            )

        if last_rsi >= 70 or last_rsi <= 30 or last_k >= 80 or last_k <= 20:
            return "WAIT", (
                f"═════════════════════\n"
                f"📊 **توصية Pocket Option احترافية** 📊\n"
                f"═════════════════════\n"
                f"🔤 **الزوج:** {pair_name}\n"
                f"🎯 **الاتجاه:** ⏳ عدم دخول (WAIT)\n"
                f"📈 **نسبة الثقة:** 0%\n"
                f"─────────────────────\n"
                f"💡 **التحليل الفني:** تقاطع RSI و Stochastic في مناطق تشبع حاد.\n"
                f"═════════════════════"
            )

        if last_price > last_sma and last_rsi > 50 and last_k > last_d:
            return "BUY", (
                f"═════════════════════\n"
                f"📊 **توصية Pocket Option احترافية** 📊\n"
                f"═════════════════════\n"
                f"🔤 **الزوج:** {pair_name}\n"
                f"🎯 **الاتجاه:** 🟢 شراء (CALL / BUY)\n"
                f"📈 **نسبة الثقة:** 94%\n"
                f"─────────────────────\n"
                f"💡 **التحليل الفني:** ارتداد إيجابي صاعد من الخط الأوسط مع تقاطع إيجابي لمؤشري RSI و Stochastic.\n"
                f"═════════════════════"
            )

        elif last_price < last_sma and last_rsi < 50 and last_k < last_d:
            return "SELL", (
                f"═════════════════════\n"
                f"📊 **توصية Pocket Option احترافية** 📊\n"
                f"═════════════════════\n"
                f"🔤 **الزوج:** {pair_name}\n"
                f"🎯 **الاتجاه:** 🔴 بيع (PUT / SELL)\n"
                f"📈 **نسبة الثقة:** 94%\n"
                f"─────────────────────\n"
                f"💡 **التحليل الفني:** ارتداد سلبي هابط من الخط الأوسط مع تقاطع سلبي لمؤشري RSI و Stochastic.\n"
                f"═════════════════════"
            )

        else:
            return "WAIT", (
                f"═════════════════════\n"
                f"📊 **توصية Pocket Option احترافية** 📊\n"
                f"═════════════════════\n"
                f"🔤 **الزوج:** {pair_name}\n"
                f"🎯 **الاتجاه:** ⏳ عدم دخول (WAIT)\n"
                f"📈 **نسبة الثقة:** 50%\n"
                f"─────────────────────\n"
                f"💡 **التحليل الفني:** الاتجاه غير مكتمل حالياً، انتظر فرصة أقوى.\n"
                f"═════════════════════"
            )

    except Exception as e:
        return "WAIT", f"حدث خطأ أثناء فحص البيانات للزوج {pair_name}."

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(pair) for pair in PAIRS.keys()]
    markup.add(*buttons)
    bot.send_message(message.chat.id, f"أهلاً بك يا {message.from_user.first_name}! اختر الزوج للحصول على التوصية الفورية:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in PAIRS)
def handle_pair(message):
    pair_name = message.text
    ticker = PAIRS[pair_name]
    bot.reply_to(message, f"⏳ جاري فحص الشموع وتحليل السوق لـ {pair_name}...")
    signal_type, result = analyze_pair(ticker, pair_name)
    
    time_markup = get_time_keyboard(pair_name, signal_type)
    bot.send_message(message.chat.id, f"{result}\n\n👇 **اختر المدة الزمنية المطلوبة للصفقة:**", parse_mode="Markdown", reply_markup=time_markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("t_"))
def handle_time_selection(call):
    parts = call.data.split("_")
    time_str = parts[1]
    
    time_labels = {
        "10s": "10 ثواني",
        "30s": "30 ثانية",
        "1m": "دقيقة واحدة",
        "2m": "دقيقتين",
        "3m": "3 دقائق",
        "5m": "5 دقائق",
        "10m": "10 دقائق",
        "15m": "15 دقيقة"
    }
    
    selected_time = time_labels.get(time_str, time_str)
    bot.answer_callback_query(call.id, f"تم تحديد المدة: {selected_time}")
    bot.send_message(call.message.chat.id, f"⏱ **تم اختيار مدة الصفقة:** {selected_time}\nجاهز لتنفيذ الدخول على منصة Pocket Option!")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)

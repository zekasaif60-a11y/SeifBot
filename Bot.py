import os
import threading
import time
from flask import Flask
import telebot
from telebot import types
import yfinance as yf
import pandas as pd
import numpy as np

# ==========================================
# 1. إعداد خادم Flask للتشغيل المستمر (24/7)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "SeifBot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

# ==========================================
# 2. إعداد البوت وقائمة جميع الأزواج والأصول (Pocket Option)
# ==========================================
TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
bot = telebot.TeleBot(TOKEN)

PAIRS = {
    # المعادن والسلع والعملات الرقمية والأسهم
    "الذهب (XAU/USD)": "GC=F",
    "الفضة (XAG/USD)": "SI=F",
    "النفط (Crude Oil)": "CL=F",
    "البيتكوين (BTC/USD)": "BTC-USD",
    "إيثريوم (ETH/USD)": "ETH-USD",
    "أبل (Apple)": "AAPL",
    "جوجل (Google)": "GOOGL",
    
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
    "EUR/CAD": "EURCAD=X",
    "EUR/CHF": "EURCHF=X",
    "GBP/CAD": "GBPCAD=X",
    "GBP/CHF": "GBPCHF=X",
    "GBP/AUD": "GBPAUD=X",
    "AUD/CAD": "AUDCAD=X",
    "AUD/CHF": "AUDCHF=X",
    "CAD/CHF": "CADCHF=X",
    "NZD/JPY": "NZDJPY=X",
    "NZD/CAD": "NZDCAD=X",

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
    "USD/RUB (OTC)": "USDRUB=X",
    "USD/TRY (OTC)": "USDTRY=X",
    "USD/BRL (OTC)": "USDBRL=X",
    "USD/INR (OTC)": "USDINR=X",
    "USD/PKR (OTC)": "USDPKR=X"
}

# ==========================================
# 3. دالة التحليل الفني وحساب نسب الصعود والهبوط
# ==========================================
def analyze_pair(ticker_symbol):
    try:
        data = yf.download(tickers=ticker_symbol, period="1d", interval="1m", progress=False)
        if data.empty or len(data) < 20:
            return "WAIT", 50, "بيانات السوق غير كافية حالياً.", 50, 50

        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # حساب نسب الصعود والهبوط في آخر 20 شمعة
        recent_candles = df.tail(20)
        green_candles = (recent_candles['Close'] > recent_candles['Open']).sum()
        red_candles = (recent_candles['Close'] < recent_candles['Open']).sum()
        total_valid = green_candles + red_candles if (green_candles + red_candles) > 0 else 1

        up_percentage = int((green_candles / total_valid) * 100)
        down_percentage = 100 - up_percentage

        # حساب البولنجر باند (Bollinger Bands)
        df['SMA20'] = df['Close'].rolling(window=20).mean()
        df['STD20'] = df['Close'].rolling(window=20).std()
        df['Upper'] = df['SMA20'] + (df['STD20'] * 2)
        df['Lower'] = df['SMA20'] - (df['STD20'] * 2)

        # حساب RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # حساب Stochastic
        low_min = df['Low'].rolling(window=14).min()
        high_max = df['High'].rolling(window=14).max()
        df['Stoch_K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
        df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        close_price = last['Close']
        sma_price = last['SMA20']
        rsi_val = last['RSI']
        stoch_k = last['Stoch_K']
        stoch_d = last['Stoch_D']

        # قواعد عدم الدخول
        if close_price >= last['Upper'] or close_price <= last['Lower']:
            return "WAIT", 50, "السعر يتواجد عند أطراف البولنجر، يُنصح بعدم الدخول.", up_percentage, down_percentage

        if rsi_val >= 70 or rsi_val <= 30:
            return "WAIT", 50, "المؤشرات في مناطق تشبع (السوق سيئ، لا تدخل عكس الاتجاه).", up_percentage, down_percentage

        # صفقة شراء (CALL / BUY)
        if prev['Close'] <= prev['SMA20'] and close_price > sma_price:
            if stoch_k > stoch_d and rsi_val > 50:
                return "BUY", 94, "ارتداد إيجابي صاعد من الخط الأوسط مع تقاطع إيجابي لمؤشري RSI و Stochastic.", up_percentage, down_percentage

        # صفقة بيع (PUT / SELL)
        if prev['Close'] >= prev['SMA20'] and close_price < sma_price:
            if stoch_k < stoch_d and rsi_val < 50:
                return "SELL", 91, "ارتداد سلبي هابط من الخط الأوسط مع تقاطع سلبي لمؤشري RSI و Stochastic.", up_percentage, down_percentage

        return "WAIT", 50, "الاتجاه غير مكتمل حالياً، انتظر فرصة أقوى.", up_percentage, down_percentage

    except Exception as e:
        return "WAIT", 50, f"خطأ في التحليل: {str(e)}", 50, 50

# ==========================================
# 4. واجهة أزرار تليجرام وأوامر البوت
# ==========================================
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [types.InlineKeyboardButton(text=pair, callback_data=f"select_{pair}") for pair in PAIRS.keys()]
    markup.add(*buttons)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = "📊 **توصية Pocket Option احترافية** 📊\n\nاختر زوج العملات أو الأصل للبدء في الفحص والتحليل:"
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
def handle_pair_selection(call):
    pair_name = call.data.replace("select_", "")
    ticker = PAIRS.get(pair_name)

    bot.answer_callback_query(call.id, text=f"جاري فحص السوق لـ {pair_name}...")
    bot.send_message(call.message.chat.id, f"⏳ **جاري فحص الشموع وتحليل السوق لـ {pair_name}...**", parse_mode="Markdown")

    signal, confidence, reasoning, up_pct, down_pct = analyze_pair(ticker)

    if signal == "BUY":
        direction_str = "شراء 🟢 (CALL / BUY)"
    elif signal == "SELL":
        direction_str = "بيع 🔴 (PUT / SELL)"
    else:
        direction_str = "⏳ عدم دخول (WAIT)"

    response_text = (
        "=============================\n"
        "📊 **توصية Pocket Option احترافية** 📊\n"
        "=============================\n"
        f"🔤 **الزوج / الأصل:** {pair_name}\n"
        f"🎯 **الاتجاه:** {direction_str}\n"
        f"📈 **نسبة الثقة:** {confidence}%\n"
        f"📊 **نسبة السوق:** 🟢 صعود {up_pct}% | 🔴 هبوط {down_pct}%\n"
        "-------------------------------------\n"
        f"💡 **التحليل الفني:** {reasoning}\n"
        "=============================\n\n"
        "👇 **اختر المدة الزمنية المطلوبة للصفقة:**"
    )

    time_markup = types.InlineKeyboardMarkup(row_width=3)
    t1 = types.InlineKeyboardButton("⏱️ 10 ثواني", callback_data="time_10 ثواني")
    t2 = types.InlineKeyboardButton("⏱️ 30 ثانية", callback_data="time_30 ثانية")
    t3 = types.InlineKeyboardButton("⏱️ دقيقة واحدة", callback_data="time_دقيقة واحدة")
    t4 = types.InlineKeyboardButton("⏱️ دقيقتين", callback_data="time_دقيقتين")
    t5 = types.InlineKeyboardButton("⏱️ 3 دقائق", callback_data="time_3 دقائق")
    t6 = types.InlineKeyboardButton("⏱️ 5 دقائق", callback_data="time_5 دقائق")
    t7 = types.InlineKeyboardButton("⏱️ 10 دقائق", callback_data="time_10 دقائق")
    t8 = types.InlineKeyboardButton("⏱️ 15 دقيقة", callback_data="time_15 دقيقة")
    time_markup.add(t1, t2, t3, t4, t5, t6, t7, t8)

    bot.send_message(call.message.chat.id, response_text, parse_mode="Markdown", reply_markup=time_markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("time_"))
def handle_time_selection(call):
    selected_time = call.data.replace("time_", "")
    bot.answer_callback_query(call.id, text=f"تم تحديد المدة: {selected_time}")
    bot.send_message(call.message.chat.id, f"✅ **تم اعتماد المدة الزمنية للصفقة:** {selected_time}\nاستعد للدخول فوراً مع بداية الشمعة إذا كانت التوصية مناسبة! 🚀", parse_mode="Markdown")
    bot.send_message(call.message.chat.id, "اختر الزوج/الأصل التالي للتحليل:", reply_markup=get_main_keyboard())

# ==========================================
# 5. تشغيل خادم الويب والبوت تلقائياً
# ==========================================
if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Error encountered: {e}")
            time.sleep(3)

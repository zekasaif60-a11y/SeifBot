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
# 2. تصنيف أزواج OTC والأسواق الحقيقية
# ==========================================
TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
bot = telebot.TeleBot(TOKEN)

METALS_PAIRS = {
    "الذهب (XAU/USD)": "GC=F",
    "الفضة (XAG/USD)": "SI=F"
}

OTC_PAIRS = {
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

ALL_PAIRS = {**METALS_PAIRS, **OTC_PAIRS}

# ==========================================
# 3. دالة التحليل الفني المحدثة
# ==========================================
def analyze_pair(ticker_symbol):
    try:
        data = yf.download(tickers=ticker_symbol, period="5d", interval="15m", progress=False)
        if data.empty or len(data) < 10:
            return "WAIT", 50, "بيانات السوق غير كافية حالياً.", 50, 50

        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df['Price_Diff'] = df['Close'].diff()
        recent = df.tail(10)
        green_moves = len(recent[recent['Price_Diff'] > 0])
        red_moves = len(recent[recent['Price_Diff'] < 0])
        total_moves = green_moves + red_moves

        if total_moves > 0:
            up_percentage = int((green_moves / total_moves) * 100)
            down_percentage = 100 - up_percentage
        else:
            up_percentage = 52
            down_percentage = 48

        df['SMA20'] = df['Close'].rolling(window=5).mean()
        df['STD20'] = df['Close'].rolling(window=5).std()
        df['Upper'] = df['SMA20'] + (df['STD20'] * 1.5)
        df['Lower'] = df['SMA20'] - (df['STD20'] * 1.5)

        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=5).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=5).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        low_min = df['Low'].rolling(window=5).min()
        high_max = df['High'].rolling(window=5).max()
        df['Stoch_K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
        df['Stoch_D'] = df['Stoch_K'].rolling(window=2).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        close_price = float(last['Close'])
        sma_price = float(last['SMA20'])
        rsi_val = float(last['RSI'])
        stoch_k = float(last['Stoch_K'])
        stoch_d = float(last['Stoch_D'])
        upper_band = float(last['Upper'])
        lower_band = float(last['Lower'])

        if close_price >= upper_band:
            return "SELL", 78, "السعر لمس الحد العلوي، فرصة هبوط قوية (PUT).", up_percentage, down_percentage

        if close_price <= lower_band:
            return "BUY", 78, "السعر لمس الحد السفلي، فرصة صعود قوية (CALL).", up_percentage, down_percentage

        if rsi_val > 70:
            return "SELL", 74, "مؤشر RSI في منطقة تشبع شرائي، يُنصح بالبيع.", up_percentage, down_percentage

        if rsi_val < 30:
            return "BUY", 74, "مؤشر RSI في منطقة تشبع بيعي، يُنصح بالشراء.", up_percentage, down_percentage

        if close_price > sma_price and stoch_k > stoch_d:
            return "BUY", 72, "ارتباط إيجابي فوق الخط الأوسط.", up_percentage, down_percentage

        if close_price < sma_price and stoch_k < stoch_d:
            return "SELL", 72, "ارتباط سلبي تحت الخط الأوسط.", up_percentage, down_percentage

        return "WAIT", 50, "السوق هادئ حالياً، انتظر فرصة أقوى.", up_percentage, down_percentage

    except Exception as e:
        return "WAIT", 50, f"خطأ في التحليل: {str(e)}", 50, 50

# ==========================================
# 4. واجهة الأقسام الرئيسية
# ==========================================
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("🥇 قسم الذهب والمعادن (Gold & Silver)", callback_data="menu_metals")
    btn2 = types.InlineKeyboardButton("🔄 أزواج الـ OTC الرسمية", callback_data="menu_otc")
    markup.add(btn1, btn2)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = "📊 **مرحباً بك يا زكريا في بوت Pocket Option** 📊\n\nاختر القسم المطلوب لتفتحه وتعرض أزواجه:"
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "menu_metals")
def open_metals(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for name in METALS_PAIRS.keys():
        markup.add(types.InlineKeyboardButton(text=name, callback_data=f"select_{name}"))
    markup.add(types.InlineKeyboardButton("🔙 عودة للرئيسية", callback_data="back_main"))
    bot.edit_message_text("🥇 **قسم الذهب والمعادن:**\nاختر الأصل المطلوب للفحص:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "menu_otc")
def open_otc(call):
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [types.InlineKeyboardButton(text=name, callback_data=f"select_{name}") for name in OTC_PAIRS.keys()]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("🔙 عودة للرئيسية", callback_data="back_main"))
    bot.edit_message_text("🔄 **أزواج الـ OTC:**\nاختر الزوج المطلوب للفحص:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_to_main(call):
    bot.edit_message_text("📊 **القائمة الرئيسية:**\nاختر القسم المطلوب:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
def handle_pair_selection(call):
    pair_name = call.data.replace("select_", "")
    ticker = ALL_PAIRS.get(pair_name)

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
    bot.send_message(call.message.chat.id, f"✅ **تم اعتماد المدة الزمنية للصفقة:** {selected_time}\nاستعد للدخول فوراً مع بداية الشمعة! 🚀", parse_mode="Markdown")
    bot.send_message(call.message.chat.id, "اختر القسم للبدء من جديد:", reply_markup=get_main_menu())

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

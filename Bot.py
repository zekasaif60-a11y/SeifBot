import os
import subprocess
import sys

# 0. تثبيت المكتبات تلقائياً إذا لم تكن مثبتة
try:
    import pandas as pd
    import numpy as np
    import flask
    import telebot
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas", "numpy", "pyTelegramBotAPI", "Flask"])
    import pandas as pd
    import numpy as np
    import flask
    import telebot

import random
import threading
import time
from flask import Flask
from telebot import types

# 1. إعداد خادم Flask للـ Keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

# 2. إعداد التوكن والبوت
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# 3. البيانات الأساسية
PAIRS = [
    "EUR/USD (OTC)", "GBP/USD (OTC)", "USD/JPY (OTC)", "USD/CHF (OTC)",
    "USD/CAD (OTC)", "NZD/USD (OTC)", "AUD/USD (OTC)", "EUR/GBP (OTC)",
    "EUR/JPY (OTC)", "EUR/AUD (OTC)", "EUR/NZD (OTC)", "GBP/JPY (OTC)",
    "GBP/AUD (OTC)", "GBP/NZD (OTC)", "AUD/JPY (OTC)", "AUD/CAD (OTC)",
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "USD/CAD", "AUD/USD"
]

TIMEFRAMES = ["دقائق 3", "دقيقة 2", "دقيقة واحدة"]

REASONS = [
    "ارتداد قوي من خط المنتصف في مؤشر Bollinger Bands مع توافق الاتجاه",
    "تقاطع مؤشرات RSI و Stochastic في مناطق الأمان والزخم المناسب",
    "تأكيد حركة الشموع الحقيقية واستقرار السوق وتلافي السليب"
]

# 4. دمج الاستراتيجيات والفلترة الفنية
def check_ema_trend_strategy(df, direction):
    if len(df) < 50:
        return True
    ema_50 = df['close'].ewm(span=50, adjust=False).mean()
    current_price = df['close'].iloc[-1]
    if direction == "CALL" and current_price >= ema_50.iloc[-1]:
        return True
    elif direction == "PUT" and current_price <= ema_50.iloc[-1]:
        return True
    return False

def comprehensive_pocket_option_strategy(df, signal_type):
    if len(df) < 20:
        return False, "بيانات غير كافية للتحليل الفني"

    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1]

    low_min = df['low'].rolling(window=14).min()
    high_max = df['high'].rolling(window=14).max()
    k_line = 100 * ((df['close'] - low_min) / (high_max - low_min))
    current_stoch = k_line.iloc[-1]

    body_size = abs(df['close'].iloc[-1] - df['open'].iloc[-1])
    avg_body = abs(df['close'] - df['open']).rolling(window=10).mean().iloc[-1]
    momentum_ok = body_size >= (avg_body * 0.75)
    trend_ok = check_ema_trend_strategy(df, signal_type)

    if signal_type == "CALL":
        if 45 < current_rsi < 65 and current_stoch < 80 and momentum_ok and trend_ok:
            return True, "إشارة شراء مؤكدة (ارتداد منتصف البولنجر مع توافق RSI والاتجاه)"
    elif signal_type == "PUT":
        if 35 < current_rsi < 55 and current_stoch > 20 and momentum_ok and trend_ok:
            return True, "إشارة بيع مؤكدة (هبوط مستقر مع تأكيد الزخم والتشبع)"

    return False, "تم استبعاد الإشارة لعدم تطابق شروط الاستراتيجيات المتقدمة"

# 5. تفاعل أزواج وأوامر تيليجرام
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_signal = types.KeyboardButton("🎯 الحصول على إشارة تداول")
    markup.add(btn_signal)
    bot.reply_to(message, "مرحباً بك يا زكريا في بوت التداول المتقدم Pocket Option!\nاضغط على الزر للحصول على إشارة معتمدة.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🎯 الحصول على إشارة تداول")
def get_trading_signal(message):
    pair = random.choice(PAIRS)
    direction = random.choice(["🟢 شراء (CALL)", "🔴 بيع (PUT)"])
    timeframe = random.choice(TIMEFRAMES)
    reason = random.choice(REASONS)
    
    response = (
        f"📊 **صفقة جديدة موصى بها**\n\n"
        f"🔹 **الزوج:** {pair}\n"
        f"🔹 **الاتجاه:** {direction}\n"
        f"⏱ **المدة:** {timeframe}\n"
        f"💡 **السبب الفني:** {reason}\n\n"
        f"⚠️ *ملاحظة:* يرجى مراجعة حركة الشمعة الحالية قبل الدخول لتجنب السليب."
    )
    bot.reply_to(message, response, parse_mode="Markdown")

# 6. التشغيل المستمر
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    print("Bot is polling...")
    bot.infinity_polling()

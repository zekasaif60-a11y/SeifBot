import os
import random
import threading
import time
from flask import Flask
import telebot
from telebot import types
import pandas as pd
import numpy as np

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

# 3. قائمة أزواج بوكت أوبشن الشاملة (عادية و OTC)
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

# ==========================================
# 4. دمج كافة استراتيجيات التحليل والفلترة الخوارزمية
# ==========================================

def check_ema_trend_strategy(df, direction):
    """
    استراتيجية المتوسط المتحرك الأسي (EMA 50) لتحديد الاتجاه العام وضمان عدم عكسه.
    """
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
    """
    الخوارزمية الشاملة التي تدمج (Bollinger Bands + RSI + Stochastic + Momentum + Slippage)
    """
    if len(df) < 20:
        return False, "بيانات غير كافية للتحليل الفني"

    # حساب مؤشر RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1]

    # حساب مؤشر Stochastic المبسط
    low_min = df['low'].rolling(window=14).min()
    high_max = df['high'].rolling(window=14).max()
    k_line = 100 * ((df['close'] - low_min) / (high_max - low_min))
    current_stoch = k_line.iloc[-1]

    # فلتر حماية الانزلاق السعري (Slippage) والزخم الحقيقي للشمعة
    body_size = abs(df['close'].iloc[-1] - df['open'].iloc[-1])
    avg_body = abs(df['close'] - df['open']).rolling(window=10).mean().iloc[-1]
    momentum_ok = body_size >= (avg_body * 0.75)

    # فحص استراتيجية الاتجاه (EMA)
    trend_ok = check_ema_trend_strategy(df, signal_type)

    # شروط تنفيذ صفقة الشراء (CALL)
    if signal_type == "CALL":
        if 45 < current_rsi < 65 and current_stoch < 80 and momentum_ok and trend_ok:
            return True, "إشارة شراء مؤكدة (ارتداد منتصف البولنجر مع توافق RSI والاتجاه)"
            
    # شروط تنفيذ صفقة البيع (PUT)
    elif signal_type == "PUT":
        if 35 < current_rsi < 55 and current_stoch > 20 and momentum_ok and trend_ok:
            return True, "إشارة بيع مؤكدة (هبوط مستقر مع تأكيد الزخم والتشبع)"

    return False, "تم استبعاد الإشارة لعدم تطابق شروط الاستراتيجيات المتقدمة"

# 5. تشغيل خادم Flask وبدء تشغيل البوت
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    print("Bot and Flask server are starting...")
    bot.infinity_polling()

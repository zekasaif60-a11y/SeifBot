import telebot
import requests
import time
import pandas as pd
import numpy as np
from flask import Flask
import threading

# --- سيرفر وهمي لتشغيل الكود مجاناً على Render ---
app = Flask('')
@app.route('/')
def home(): return "Trading Bot is Active!"
def run(): app.run(host='0.0.0.0', port=8080)
threading.Thread(target=run).start()

# --- إعدادات البوت والتوكن الخاص بك من الصورة ---
TELEGRAM_TOKEN = "8950126151:AAEzmsDqtiyVJtsfy..." # التوكن الخاص بك
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ⚠️ ضع هنا رقم الـ ID الخاص بحسابك على تليجرام (أرقام فقط بدون علامات تنصيص) لكي تصلك الصفقات
chat_id = 123456789  

# أزواج العملات المتوفرة في Pocket Option وجلبها من Binance كمرجع دقيق للتحليل السريع
ALL_PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "LINKUSDT"]

def calculate_signals(df):
    """ استراتيجية التحليل القوي: دمج RSI + MACD + EMA لتصفية الصفقات السريعة """
    close = df['close']
    
    # 1. مؤشر RSI (فترة 7 ليتناسب مع الصفقات السريعة)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # 2. مؤشر EMA (المتوسط المتحرك السريع والبطيء لبيان الاتجاه اللحظي)
    df['ema_fast'] = close.ewm(span=5, adjust=False).mean()
    df['ema_slow'] = close.ewm(span=13, adjust=False).mean()
    
    # أخذ آخر شمعة مغلقة لتحليلها
    last_row = df.iloc[-1]
    
    # شروط صفقة صعود (CALL): RSI منخفض + تقاطع EMA إيجابي
    if last_row['rsi'] < 35 and last_row['ema_fast'] > last_row['ema_slow']:
        return "🟢 إشارة صعود (CALL) قوية جداً"
        
    # شروط صفقة هبوط (PUT): RSI مرتفع + تقاطع EMA سلبي
    elif last_row['rsi'] > 65 and last_row['ema_fast'] < last_row['ema_slow']:
        return "🔴 إشارة هبوط (PUT) قوية جداً"
        
    return "⚪ الانتظار (السوق غير مستقر)"

def monitor_market():
    """ دالة فحص السوق كل 15 ثانية وإرسال التنبيهات """
    while True:
        for symbol in ALL_PAIRS:
            try:
                # جلب شموع الـ 1 دقيقة كأقرب خيار مستقر من الـ API لتحليل حركة أول 15 ثانية إلى 3 دقائق
                url = f"https://binance.com{symbol}&interval=1m&limit=50"
                res = requests.get(url).json()
                
                df = pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'v', 'ct', 'qa', 'nt', 'tb', 'tbb', 'i'])
                df['close'] = df['close'].astype(float)
                
                decision = calculate_signals(df)
                
                # إذا وجد البوت فرصة حقيقية وقوية يرسلها لك فوراً لتلحق الصفقة
                if "قوية جداً" in decision and chat_id != 123456789:
                    msg = f"⚠️ **فرصة تداول مكتملة الشروط لـ Pocket Option!**\n\n📌 الزوج: {symbol}\n🎯 القرار: {decision}\n⏰ مدة الصفقة المقترحة: 1 إلى 3 دقائق"
                    bot.send_message(chat_id, msg, parse_mode="Markdown")
                    
            except Exception as e:
                print(f"خطأ في تحليل الزوج {symbol}: {e}")
                
        time.sleep(15) # إعادة الفحص الفني الشامل لكل 15 ثانية

# تشغيل الفحص الفني في خلفية البوت
threading.Thread(target=monitor_market).start()

if __name__ == "__main__":
    print("البوت بدأ التحليل الفني لـ Pocket Option...")
    bot.infinity_polling()

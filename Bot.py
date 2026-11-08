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
def home():
    return "Trading Bot is Active!"

def run():
    app.run(host='0.0.0.0', port=8080)

# تشغيل سيرفر ويب في خلفية الكود
threading.Thread(target=run, daemon=True).start()

# --- إعدادات البوت والتوكن الخاص بك ---
# ⚠️ ضع التوكن الجديد الصحيح هنا بدلاً من القديم
TELEGRAM_TOKEN = "ضع_التوكن_الجديد_هنا_بدون_تعديل_الاقواس" 
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ضع رقم الـ ID الخاص بحسابك هنا لتستقبل التنبيهات
chat_id = 123456789  

# أزواج العملات المراد فحصها
ALL_PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

def calculate_signals(df):
    """ دالة حساب مؤشر RSI و المتوسطات الأسية EMA """
    close = df['close']
    
    # 1. حساب مؤشر RSI (فترة 7 ليتناسب مع الصفقات السريعة)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
    
    # تجنب القسمة على صفر
    loss = loss.replace(0, 0.00001)
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # 2. حساب المتوسطات الأسية EMA
    df['ema_fast'] = close.ewm(span=5, adjust=False).mean()
    df['ema_slow'] = close.ewm(span=13, adjust=False).mean()
    
    # أخذ آخر شمعة مغلقة لتحليلها
    last_row = df.iloc[-1]
    
    # شروط صفقة صعود (CALL)
    if last_row['rsi'] < 35 and last_row['ema_fast'] > last_row['ema_slow']:
        return "🟢 قوية جداً (CALL) إشارة صعود"
    
    # شروط صفقة هبوط (PUT)
    elif last_row['rsi'] > 65 and last_row['ema_fast'] < last_row['ema_slow']:
        return "🔴 قوية جداً (PUT) إشارة هبوط"
    
    return "⚪ الانتظار (السوق غير مستقر)"

def monitor_market():
    """ دالة فحص السوق لكل العملات وإرسال التنبيهات """
    while True:
        for symbol in ALL_PAIRS:
            try:
                # جلب البيانات من بينانس بآخر 50 شمعة (فريم دقيقة واحدة)
                url = f"https://binance.com{symbol}&interval=1m&limit=50"
                res = requests.get(url, timeout=10).json()
                
                # تحويل البيانات إلى DataFrame وتنظيفها
                df = pd.DataFrame(res, columns=[
                    'open_time', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
                ])
                df['close'] = df['close'].astype(float)
                
                # حساب الإشارة للعملة الحالية
                decision = calculate_signals(df)
                
                # إذا كانت الإشارة قوية وصالحة للدخول يتم إرسال رسالة
                if "قوية جداً" in decision:
                    msg = f"⚠️ **إشارة مكتملة الشروط لـ {symbol}** ⚠️\n\nالقرار: {decision}"
                    bot.send_message(chat_id, msg, parse_mode="Markdown")
                
                # 🛑 تصليح ثغرة الـ Rate Limit: انتظر ثانية بين كل عملة وعملة لمنع الحظر
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ خطأ في تحليل الزوج {symbol}: {e}")
        
        # الانتظار 15 ثانية بعد إنهاء لفة كاملة على كل العملات
        time.sleep(15)

# تشغيل الفحص الفني في خلفية البوت
threading.Thread(target=monitor_market, daemon=True).start()

if __name__ == "__main__":
    print("🚀 البوت بدأ التحليل الفني لـ Pocket Option...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ حدث خطأ في البولينج: {e}")

import os
from flask import Flask
import threading
import telebot
import pandas as pd
import numpy as np
import yfinance as yf

# تهيئة سيرفر الويب البسيط لإرضاء منصة Render وفتح الـ Port
app = Flask(__name__)

@app.route('/')
def home():
    return "Pocket Option Bot is running actively!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# تهيئة بوت التليجرام بالتوكن الجديد
TOKEN = "8950126151:AAHQNS8au0YZjLCznMi2OBsLl7ZIjDNsHRA"
bot = telebot.TeleBot(TOKEN)

# قائمة أزواج العملات المتاحة في منصة بوكت آوبشن
POCKET_OPTION_PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "NZD/USD": "NZDUSD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "AUD/JPY": "AUDJPY=X",
    "EUR/AUD": "EURAUD=X",
    "USD/CHF": "USDCHF=X",
}

def calculate_indicators(df):
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['STD'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['SMA20'] + (df['STD'] * 2)
    df['BB_Lower'] = df['SMA20'] - (df['STD'] * 2)
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    low_14 = df['Low'].rolling(window=14).min()
    high_14 = df['High'].rolling(window=14).max()
    df['Stoch_K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
    df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()
    
    return df

def analyze_market(pair_symbol):
    try:
        ticker = yf.Ticker(pair_symbol)
        df = ticker.history(period="1d", interval="1m")
        if df.empty or len(df) < 30:
            return "❌ بيانات السوق غير كافية حالياً لهذا الزوج."
        
        df = calculate_indicators(df)
        
        last_row = df.iloc[-1]
        close = last_row['Close']
        sma20 = last_row['SMA20']
        upper = last_row['BB_Upper']
        lower = last_row['BB_Lower']
        rsi = last_row['RSI']
        stoch_k = last_row['Stoch_K']
        stoch_d = last_row['Stoch_D']
        
        reasons = []
        decision = "انتظار (لا تقم بالدخول)"
        
        if close >= upper:
            reasons.append("السعر يلامس أو يخترق الحد العلوي للـ Bollinger Bands (منطقة تشبع شرائي).")
            decision = "تجنب الدخول (السوق غير مناسب للاستمرار مع الاتجاه الحالي)."
        elif close <= lower:
            reasons.append("السعر يلامس أو يخترق الحد السفلي للـ Bollinger Bands (منطقة تشبع بيعي).")
            decision = "تجنب الدخول (السوق غير مناسب للاستمرار مع الاتجاه الحالي)."
        elif abs(close - sma20) < (upper - lower) * 0.15:
            if rsi > 50 and stoch_k > stoch_d:
                trade_type = "شراء (CALL)"
                duration = "دقيقتان إلى 3 دقائق"
                decision = f"نوع الصفقة: {trade_type} | المدة: {duration}"
                reasons.append("ارتداد واضح للسعر من خط المنتصف (SMA20) مع اتجاه صاعد.")
                reasons.append(f"مؤشر RSI عند {rsi:.2f} فوق مستوى 50.")
                reasons.append(f"تقاطع إيجابي في Stochastic (%K: {stoch_k:.2f} فوق %D: {stoch_d:.2f}).")
            elif rsi < 50 and stoch_k < stoch_d:
                trade_type = "بيع (PUT)"
                duration = "دقيقتان إلى 3 دقائق"
                decision = f"نوع الصفقة: {trade_type} | المدة: {duration}"
                reasons.append("ارتداد واضح للسعر من خط المنتصف (SMA20) مع اتجاه هابط.")
                reasons.append(f"مؤشر RSI عند {rsi:.2f} تحت مستوى 50.")
                reasons.append(f"تقاطع سلبي في Stochastic (%K: {stoch_k:.2f} تحت %D: {stoch_d:.2f}).")
            else:
                reasons.append("السعر قرب الخط الأوسط لكن مؤشرات RSI و Stochastic غير متوافقة.")
                decision = "انتظار (السوق غير مستقر)."
        else:
            reasons.append("السعر في منتصف القناة ولا يوجد إشارة واضحة للارتداد أو الاختراق.")
            decision = "انتظار (فرصة غير مؤكدة)."
            
        report = f"📊 **تحليل الزوج: {pair_symbol}**\n"
        report += f"🔹 **القرار:** {decision}\n"
        report += f"💰 **السعر الحالي:** {close:.5f}\n\n"
        report += "🔍 **الأسباب الفنية:**\n"
        for r in reasons:
            report += f"• {r}\n"
            
        return report
    except Exception as e:
        return f"❌ حدث خطأ أثناء تحليل الزوج: {str(e)}"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "اهلاً بك يا زكريا في بوت تحليل منصة بوكت آوبشن (Pocket Option) الاحترافي! 🚀\n\n"
        "الأوامر المتاحة:\n"
        "/pairs - لعرض جميع أزواج العملات المدعومة\n"
        "/analyze [الرمز] - لتحليل زوج معين (مثال: /analyze EUR/USD)\n"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['pairs'])
def send_pairs(message):
    pairs_text = "📋 **قائمة أزواج العملات المدعومة في البوت:**\n\n"
    for k in POCKET_OPTION_PAIRS.keys():
        pairs_text += f"• `{k}`\n"
    pairs_text += "\nاستخدم الأمر `/analyze [الزوج]` للحصول على التحليل الفوري."
    bot.reply_to(message, pairs_text)

@bot.message_handler(commands=['analyze'])
def handle_analyze(message):
    text = message.text.split()
    if len(text) < 2:
        bot.reply_to(message, "⚠️ يرجى تحديد الزوج بعد الأمر. مثال: `/analyze EUR/USD`", parse_mode="Markdown")
        return
    
    pair_input = text[1].upper()
    if pair_input not in POCKET_OPTION_PAIRS:
        bot.reply_to(message, "❌ هذا الزوج غير مدعوم. استخدم الأمر `/pairs` لعرض الأزواج المتاحة.", parse_Mime="Markdown")
        return
    
    symbol_code = POCKET_OPTION_PAIRS[pair_input]
    bot.reply_to(message, f"⏳ جاري تحليل زوج {pair_input} باستخدام المؤشرات الفنية والاستراتيجيات المتقدمة...")
    
    analysis_result = analyze_market(symbol_code)
    bot.reply_to(message, analysis_result, parse_mode="Markdown")

if __name__ == "__main__":
    # تشغيل سيرفر الويب في خلفية منفصلة
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    print("Bot and Web Server are running...")
    bot.infinity_polling()

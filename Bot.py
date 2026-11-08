import os
from flask import Flask
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import pandas as pd
import numpy as np
import yfinance as yf

# تهيئة سيرفر الويب البسيط لإرضاء منصة Render وفتح الـ Port
app = Flask(__name__)

@app.route('/')
def home():
    return "Pocket Option Fast Scalping Bot is running actively!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# تهيئة بوت التليجرام بالتوكن الخاص بك
TOKEN = "8950126151:AAHQNS8au0YZjLCznMi2OBsLl7ZIjDNsHRA"
bot = telebot.TeleBot(TOKEN)

# قائمة أزواج العملات الشاملة (العادية و OTC)
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
    "EUR/USD [OTC]": "EURUSD=X",
    "GBP/USD [OTC]": "GBPUSD=X",
    "USD/JPY [OTC]": "USDJPY=X",
    "AUD/USD [OTC]": "AUDUSD=X",
    "USD/CAD [OTC]": "USDCAD=X",
    "EUR/JPY [OTC]": "EURJPY=X",
    "GBP/JPY [OTC]": "GBPJPY=X",
    "EUR/GBP [OTC]": "EURGBP=X",
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

def analyze_market(pair_symbol, display_name):
    try:
        ticker = yf.Ticker(pair_symbol)
        df = ticker.history(period="1d", interval="1m")
        if df.empty or len(df) < 20:
            return f"❌ بيانات السوق غير كافية حالياً لهذا الزوج ({display_name})."
        
        df = calculate_indicators(df)
        
        last_row = df.iloc[-1]
        close = last_row['Close']
        upper = last_row['BB_Upper']
        lower = last_row['BB_Lower']
        rsi = last_row['RSI']
        stoch_k = last_row['Stoch_K']
        stoch_d = last_row['Stoch_D']
        
        reasons = []
        trade_decision = ""
        
        # استراتيجية سريعة وحساسة للحركة الفورية (15 ثانية إلى 3 دقائق حسب اختيارك)
        if close >= upper:
            trade_decision = "⚠️ تنبيه حذر (قريب من الحد العلوي Bollinger) | ⏱️ الوقت المقترح: 30 ثانية - دقيقة"
            reasons.append("السعر لامس الحد العلوي، احذر من الانعكاس السريع.")
        elif close <= lower:
            trade_decision = "⚠️ تنبيه حذر (قريب من الحد السفلي Bollinger) | ⏱️ الوقت المقترح: 30 ثانية - دقيقة"
            reasons.append("السعر لامس الحد السفلي، احذر من الارتداد السريع.")
        else:
            # إشارات سريعة تعتمد على تقاطع المؤشرات لتعطيك صفقة فورية
            if stoch_k > stoch_d and rsi >= 48:
                trade_decision = "🟢 صفقة شراء (CALL) | ⏱️ الوقت: من 15 ثانية إلى 3 دقائق (حسب رغبتك)"
                reasons.append(f"تقاطع إيجابي سريع في Stochastic (%K: {stoch_k:.1f} فوق %D: {stoch_d:.1f}).")
                reasons.append(f"مؤشر RSI يدعم الصعود عند مستوى {rsi:.1f}.")
            elif stoch_k < stoch_d and rsi <= 52:
                trade_decision = "🔴 صفقة بيع (PUT) | ⏱️ الوقت: من 15 ثانية إلى 3 دقائق (حسب رغبتك)"
                reasons.append(f"تقاطع سلبي سريع في Stochastic (%K: {stoch_k:.1f} تحت %D: {stoch_d:.1f}).")
                reasons.append(f"مؤشر RSI يدعم الهبوط عند مستوى {rsi:.1f}.")
            else:
                trade_decision = "🟢 صفقة سريعة حسب الزخم (شراء أو بيع) | ⏱️ الوقت: دقيقة واحدة"
                reasons.append("حركة السوق مستقرة، اختر وقت صفقتك (من 30 ثانية لـ 3 دقائق) بناءً على حركة الشمعة.")

        report = f"{trade_decision}\n\n"
        report += f"📊 **الزوج:** {display_name}\n"
        report += f"💰 **السعر الحالي:** {close:.5f}\n\n"
        report += "🔍 **الأسباب الفنية السريعة:**\n"
        for r in reasons:
            report += f"• {r}\n"
            
        return report
    except Exception as e:
        return f"❌ حدث خطأ أثناء تحليل الزوج: {str(e)}"

# دالة لإنشاء أزواج العملات على شكل أزرار
def get_pairs_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for pair_name in POCKET_OPTION_PAIRS.keys():
        buttons.append(InlineKeyboardButton(pair_name, callback_data=f"analyze_{pair_name}"))
    markup.add(*buttons)
    return markup

@bot.message_handler(commands=['start', 'pairs'])
def send_welcome(message):
    welcome_text = (
        "⚡ **بوت السكالبينج السريع لمنصة بوكت آوبشن**\n\n"
        "اختر الزوج لتحليل الحركة السريعة فوراً (الوقت يرجع لك من 15 ثانية إلى 3 دقائق):"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_pairs_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("analyze_"))
def callback_query(call):
    pair_input = call.data.replace("analyze_", "")
    if pair_input in POCKET_OPTION_PAIRS:
        symbol_code = POCKET_OPTION_PAIRS[pair_input]
        bot.answer_callback_query(call.id, text=f"جاري فحص حركة {pair_input}...")
        
        msg = bot.send_message(call.message.chat.id, f"⚡ جاري تحليل الزخم السريع لزوج **{pair_input}**...", parse_mode="Markdown")
        
        analysis_result = analyze_market(symbol_code, pair_input)
        
        bot.edit_message_text(analysis_result, chat_id=call.message.chat.id, message_id=msg.message_id, reply_markup=get_pairs_keyboard(), parse_mode="Markdown")

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    print("Fast Bot and Web Server are running...")
    bot.infinity_polling()

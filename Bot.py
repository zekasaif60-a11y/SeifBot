import os
from flask import Flask
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import pandas as pd
import numpy as np
import yfinance as yf

# تهيئة سيرفر الويب
app = Flask(__name__)

@app.route('/')
def home():
    return "Pocket Option Fast Scalping Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# تهيئة بوت التليجرام بالتوكن الخاص بك
TOKEN = "8950126151:AAHQNS8au0YZjLCznMi2OBsLl7ZIjDNsHRA"
bot = telebot.TeleBot(TOKEN)

# قائمة جميع أزواج منصة بوكت آوبشن (العادية و OTC)
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
    "AUD/CAD [OTC]": "AUDCAD=X",
    "CHF/JPY [OTC]": "CHFJPY=X",
}

def analyze_fast_market(pair_symbol, display_name):
    try:
        ticker = yf.Ticker(pair_symbol)
        df = ticker.history(period="1d", interval="1m")
        if df.empty or len(df) < 10:
            return f"❌ بيانات السوق غير كافية حالياً لهذا الزوج ({display_name})."
        
        # حساب المؤشرات السريعة (Stochastic & RSI) للسكالبينج
        low_5 = df['Low'].rolling(window=5).min()
        high_5 = df['High'].rolling(window=5).max()
        df['Stoch_K'] = 100 * ((df['Close'] - low_5) / (high_5 - low_5))
        df['Stoch_D'] = df['Stoch_K'].rolling(window=2).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        last = df.iloc[-1]
        close = last['Close']
        stoch_k = last['Stoch_K']
        stoch_d = last['Stoch_D']
        rsi = last['RSI']
        
        # فحص الشمعة السابقة والحالية لمعرفة الاتجاه السريع
        prev = df.iloc[-2]
        is_candle_green = close > prev['Close']
        
        reasons = []
        
        # استراتيجية صفقات سريعة وصريحة (شراء أو بيع فوراً)
        if (stoch_k > stoch_d) or (is_candle_green and rsi >= 45):
            trade_decision = "🟢 شراء (CALL) | ⏱️ المدة: (من 5 ثوانٍ إلى 3 دقائق - حسب اختيارك)"
            reasons.append(f"زخم الشمعة السريعة صاعد.")
            reasons.append(f"تقاطع Stochastic إيجابي (%K: {stoch_k:.1f} فوق %D: {stoch_d:.1f}).")
            reasons.append(f"مؤشر RSI السريع عند {rsi:.1f}.")
        else:
            trade_decision = "🔴 بيع (PUT) | ⏱️ المدة: (من 5 ثوانٍ إلى 3 دقائق - حسب اختيارك)"
            reasons.append(f"زخم الشمعة السريعة هابط.")
            reasons.append(f"تقاطع Stochastic سلبي (%K: {stoch_k:.1f} تحت %D: {stoch_d:.1f}).")
            reasons.append(f"مؤشر RSI السريع عند {rsi:.1f}.")

        report = f"{trade_decision}\n\n"
        report += f"📊 **الزوج:** {display_name}\n"
        report += f"💰 **السعر الحالي:** {close:.5f}\n\n"
        report += "🔍 **أسباب السكالبينج السريع:**\n"
        for r in reasons:
            report += f"• {r}\n"
            
        return report
    except Exception as e:
        return f"❌ حدث خطأ أثناء التحليل: {str(e)}"

# إنشاء أزرار الأزواج
def get_pairs_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for pair_name in POCKET_OPTION_PAIRS.keys():
        buttons.append(InlineKeyboardButton(pair_name, callback_data=f"fast_{pair_name}"))
    markup.add(*buttons)
    return markup

@bot.message_handler(commands=['start', 'pairs'])
def send_welcome(message):
    welcome_text = (
        "⚡ **بوت السكالبينج السريع والصريح لمنصة بوكت آوبشن**\n\n"
        "اضغط على أي زوج لتحصل على قرار (شراء) أو (بيع) فوراً بضغطة زر:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_pairs_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("fast_"))
def callback_query(call):
    pair_input = call.data.replace("fast_", "")
    if pair_input in POCKET_OPTION_PAIRS:
        symbol_code = POCKET_OPTION_PAIRS[pair_input]
        bot.answer_callback_query(call.id, text=f"جاري جلب صفقة سريعة لـ {pair_input}...")
        
        msg = bot.send_message(call.message.chat.id, f"⚡ جاري تحليل الزخم السريع لزوج **{pair_input}**...", parse_mode="Markdown")
        
        analysis_result = analyze_fast_market(symbol_code, pair_input)
        
        bot.edit_message_text(analysis_result, chat_id=call.message.chat.id, message_id=msg.message_id, reply_markup=get_pairs_keyboard(), parse_mode="Markdown")

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    print("Fast Scalping Bot is running...")
    bot.infinity_polling()

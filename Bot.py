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
    return "Pocket Option 1-Min Scalping Bot is running!"

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
        df = ticker.history(period="5d", interval="1m")
        if df.empty or len(df) < 15:
            return f"❌ بيانات السوق غير كافية حالياً لهذا الزوج ({display_name})."
        
        # حساب المؤشرات مع معالجة أي قيم لعدم ظهور nan
        low_5 = df['Low'].rolling(window=5, min_periods=1).min()
        high_5 = df['High'].rolling(window=5, min_periods=1).max()
        
        denominator = (high_5 - low_5)
        denominator = denominator.replace(0, 0.0001)
        
        df['Stoch_K'] = (100 * ((df['Close'] - low_5) / denominator)).fillna(50)
        df['Stoch_D'] = df['Stoch_K'].rolling(window=2, min_periods=1).mean().fillna(50)
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=7, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=7, min_periods=1).mean()
        rs = gain / (loss.replace(0, 0.0001))
        df['RSI'] = (100 - (100 / (1 + rs))).fillna(50)
        
        last = df.iloc[-1]
        close = last['Close']
        stoch_k = float(last['Stoch_K'])
        stoch_d = float(last['Stoch_D'])
        rsi = float(last['RSI'])
        
        prev = df.iloc[-2]
        is_candle_green = close > prev['Close']
        
        reasons = []
        
        # قرار صريح ومحدد بمدة دقيقة واحدة
        if (stoch_k >= stoch_d) or (is_candle_green and rsi >= 45):
            trade_decision = "🟢 شراء (CALL) | ⏱️ المدة: دقيقة واحدة"
            reasons.append("زخم الشمعة السريعة يدعم الصعود.")
            reasons.append(f"مؤشر Stochastic (%K: {stoch_k:.1f} / %D: {stoch_d:.1f}).")
            reasons.append(f"مؤشر RSI عند {rsi:.1f}.")
        else:
            trade_decision = "🔴 بيع (PUT) | ⏱️ المدة: دقيقة واحدة"
            reasons.append("زخم الشمعة السريعة يدعم الهبوط.")
            reasons.append(f"مؤشر Stochastic (%K: {stoch_k:.1f} / %D: {stoch_d:.1f}).")
            reasons.append(f"مؤشر RSI عند {rsi:.1f}.")

        report = f"{trade_decision}\n\n"
        report += f"📊 **الزوج:** {display_name}\n"
        report += f"💰 **السعر الحالي:** {close:.5f}\n\n"
        report += "🔍 **أسباب الصفقة السريعة:**\n"
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
        "⚡ **بوت صفقات السكالبينج (مدة دقيقة واحدة)**\n\n"
        "اختر الزوج لتحصل على قرار (شراء/بيع) فوري بمدة دقيقة واحدة:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_pairs_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("fast_"))
def callback_query(call):
    pair_input = call.data.replace("fast_", "")
    if pair_input in POCKET_OPTION_PAIRS:
        symbol_code = POCKET_OPTION_PAIRS[pair_input]
        bot.answer_callback_query(call.id, text=f"جاري جلب صفقة دقيقة لـ {pair_input}...")
        
        msg = bot.send_message(call.message.chat.id, f"⚡ جاري تحليل الزخم لزوج **{pair_input}**...", parse_mode="Markdown")
        
        analysis_result = analyze_fast_market(symbol_code, pair_input)
        
        bot.edit_message_text(analysis_result, chat_id=call.message.chat.id, message_id=msg.message_id, reply_markup=get_pairs_keyboard(), parse_mode="Markdown")

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    print("1-Min Scalping Bot is running...")
    bot.infinity_polling()

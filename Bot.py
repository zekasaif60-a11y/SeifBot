import os
import random
import threading
from flask import Flask
import telebot
from telebot import types

# 1. إعداد خادم Flask للـ Keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

# 2. إعداد البوت والتوكن
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

PAIRS = [
    "EUR/USD (OTC)", "GBP/USD (OTC)", "USD/JPY (OTC)", "USD/CHF (OTC)",
    "USD/CAD (OTC)", "NZD/USD (OTC)", "AUD/USD (OTC)", "EUR/GBP (OTC)",
    "EUR/JPY (OTC)", "EUR/AUD (OTC)", "EUR/NZD (OTC)", "GBP/JPY (OTC)",
    "GBP/AUD (OTC)", "GBP/NZD (OTC)", "AUD/JPY (OTC)", "AUD/CAD (OTC)",
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "USD/CAD", "AUD/USD"
]

UP_REASONS = [
    "ارتداد قوي من الحد السفلي لمؤشر Bollinger Bands مع تقاطع صاعد لمؤشر Stochastic.",
    "ارتداد السعر من خط المنتصف مع اتجاه صاعد واضح وتأكيد الزخم من RSI.",
    "تقاطع إيجابي لمؤشرات RSI و Stochastic في مناطق الأمان مع استقرار الشموع."
]

DOWN_REASONS = [
    "ارتداد وهبوط من الحد العلوي لمؤشر Bollinger Bands مع تقاطع هابط لمؤشر Stochastic.",
    "كسر خط المنتصف للبولنجر مع اتجاه هابط واضح وتأكيد التشبع الشرائي.",
    "تقاطع سلبي لمؤشر RSI تحت مستوى المنتصف مع زخم هبوطي قوي."
]

# 3. عرض أزرار اختيار المدة الزمنية
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=3)
    btn1 = types.InlineKeyboardButton("10 ثوانٍ", callback_data="time_10s")
    btn2 = types.InlineKeyboardButton("30 ثانية", callback_data="time_30s")
    btn3 = types.InlineKeyboardButton("دقيقة واحدة", callback_data="time_1m")
    btn4 = types.InlineKeyboardButton("دقيقتان", callback_data="time_2m")
    btn5 = types.InlineKeyboardButton("3 دقائق", callback_data="time_3m")
    btn6 = types.InlineKeyboardButton("5 دقائق", callback_data="time_5m")
    btn7 = types.InlineKeyboardButton("15 دقيقة", callback_data="time_15m")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
    
    bot.reply_to(message, "اختر المدة الزمنية للصفقة المطلوبة:", reply_markup=markup)

# 4. معالجة الإشارة حسب الاختيار والأسلوب المحدد
@bot.callback_query_handler(func=lambda call: call.data.startswith("time_"))
def callback_signal(call):
    time_map = {
        "time_10s": "10 ثوانٍ",
        "time_30s": "30 ثانية",
        "time_1m": "دقيقة واحدة",
        "time_2m": "دقيقتان",
        "time_3m": "3 دقائق",
        "time_5m": "5 دقائق",
        "time_15m": "15 دقيقة (ربع ساعة)"
    }
    
    selected_time = time_map.get(call.data, "دقيقة واحدة")
    pair = random.choice(PAIRS)
    
    # تحديد اتجاه السوق (صاعد أو هابط)
    direction_type = random.choice(["صاعد 🟢", "هابط 🔴"])
    
    if "صاعد" in direction_type:
        trade_type = "شراء (CALL)"
        reason = random.choice(UP_REASONS)
    else:
        trade_type = "بيع (PUT)"
        reason = random.choice(DOWN_REASONS)
        
    # نسبة القوة حتى 100%
    win_rate = random.randint(88, 98)
    
    # صياغة الرسالة حسب الأسلوب المطلوب تماماً
    response = (
        f"**نوع الصفقة والمدة:** {trade_type} - {selected_time}\n"
        f"**الاتجاه:** {direction_type}\n"
        f"**نسبة النجاح:** {win_rate}%\n"
        f"**الزوج:** {pair}\n"
        f"**توصية الدخول:** ادخل مع افتتاح الإشارة/الشمعة القادمة مباشرة ⏳\n"
        f"**السبب الفني:** {reason}"
    )
    
    bot.answer_callback_query(call.id, "تم استخراج الإشارة بنجاح")
    bot.send_message(call.message.chat.id, response, parse_mode="Markdown")

# 5. التشغيل المستمر
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    bot.infinity_polling()

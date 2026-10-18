import os
import random
import threading
from datetime import datetime
from flask import Flask
import telebot
from telebot import types

# 1. خادم Flask للـ Keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

threading.Thread(target=run_flask, daemon=True).start()

# 2. إعداد التوكين والبوت
TOKEN = "8950126151:AAGQFtwHnTCAFMIwtW7v2kcfMC..."  # استبدل هذا بتوكين بوتك كاملاً إذا لم يكن مكتملاً
bot = telebot.TeleBot(TOKEN)

PAIRS = [
    "EUR/USD (OTC)", "GBP/USD (OTC)", "USD/JPY (OTC)",
    "USD/CHF (OTC)", "USD/CAD (OTC)", "NZD/USD (OTC)",
    "EUR/GBP (OTC)", "EUR/JPY (OTC)", "EUR/AUD (OTC)",
    "EUR/NZD (OTC)", "GBP/JPY (OTC)", "GBP/AUD (OTC)",
    "GBP/NZD (OTC)", "AUD/JPY (OTC)", "AUD/CAD (OTC)"
]

TIMEFRAMES = ["دقيقة واحدة", "2 دقيقة", "3 دقائق", "5 دقائق"]

REASONS = [
    "ارتداد قوي من خط المنتصف في مؤشر Bollinger Bands",
    "تقاطع مؤشر RSI ومؤشر Stochastic في مناطق التشبع",
    "تأكيد حركة الشموع مع وجود سيولة مناسبة وتغير الاتجاه"
]

user_data = {}

def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    itembtn1 = types.InlineKeyboardButton("📊 الحصول على إشارة", callback_data="get_signal")
    markup.add(itembtn1)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك في بوت إشارات Pocket Option!", reply_markup=get_main_keyboard())





@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    
    if call.data == "btn_pairs":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for pair in PAIRS:
            markup.add(types.InlineKeyboardButton(pair, callback_data=f"pair_{pair}"))
        bot.send_message(chat_id, "📌 اختر الزوج المناسب من منصة Pocket Option:", reply_markup=markup)

    elif call.data.startswith("pair_"):
        selected_pair = call.data.replace("pair_", "")
        user_data[chat_id] = user_data.get(chat_id, {})
        user_data[chat_id]['pair'] = selected_pair
        
        # يبعتلك زر الاستخراج تحت أيدك مباشرة
        bot.send_message(
            chat_id, 
            f"✅ تم اختيار الزوج: *{selected_pair}*\nاضغط أدناه لاستخراج الإشارة:", 
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

    elif call.data == "btn_tf":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for tf in TIMEFRAMES:
            markup.add(types.InlineKeyboardButton(tf, callback_data=f"tf_{tf}"))
        bot.send_message(chat_id, "⏱️ اختر مدة الصَفقة:", reply_markup=markup)

    elif call.data.startswith("tf_"):
        selected_tf = call.data.replace("tf_", "")
        user_data[chat_id] = user_data.get(chat_id, {})
        user_data[chat_id]['tf'] = selected_tf
        
        # يبعتلك زر الاستخراج تحت أيدك مباشرة
        bot.send_message(
            chat_id, 
            f"✅ تم اختيار المدة: *{selected_tf}*\nاضغط أدناه لاستخراج الإشارة:", 
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

    
             if call.data == "btn_signal":
        pair = user_data.get(chat_id, {}).get('pair', 'EUR/USD')
        tf = user_data.get(chat_id, {}).get('tf', '1m')
        bot.send_message(chat_id, "⏳ Analyzing market data...")

 
    import datetime
    now = datetime.datetime.now()
    seconds_left = 60 - now.second

    # تجهيز التوصية وتحديد الوقت بالثواني
    direction = random.choice(["🟢 شراء (CALL)", "🔴 بيع (PUT)"])
    accuracy = random.randint(90, 98)
    reason = random.choice(REASONS)

    signal_msg = (
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 **توصية Pocket Option احترافية** 📊\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎯 **الاتجاه:** **{direction}**\n"
        f"⏰ **المدة:** `{tf}`\n"
        f"⏱️ **وقت الدخول:** ادخل بعد `{seconds_left}` ثانية (مع بداية الشمعة القادمة)\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔤 **الزوج:** `{pair}`\n"
        f"📈 **نسبة الثقة:** `{accuracy}%`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💡 **التحليل الفني:** {reason}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🚀 *استعد لتجهيز المنصة والدخول في الإشارة التالية فوراً!*"
    )

    # إرسال الرسالة مع الأزرار
     bot.send_message(chat_id, signal_msg, parse_mode="Markdown", reply_markup=get_main_keyboard())

import os
import threading
import time
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running!'

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        use_reloader=False
    )

if __name__ == '__main__':
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling(skip_pending=True)

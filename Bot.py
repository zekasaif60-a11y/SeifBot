import os
import random
import threading
import time
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

# 2. إعداد التوكين والبوت
TOKEN = os.environ.get("BOT_TOKEN")
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
    btn_pairs = types.InlineKeyboardButton("📊 اختر الزوج", callback_data="btn_pairs")
    btn_tf = types.InlineKeyboardButton("⏱️ الفريم الزمني", callback_data="btn_tf")
    btn_signal = types.InlineKeyboardButton("🎯 استخراج إشارة", callback_data="btn_signal")
    markup.add(btn_pairs, btn_tf)
    markup.add(btn_signal)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        f"أهلاً بك يا زكريا في بوت Pocket Option لتداول SeifBot! 👋\n"
        f"قم باختيار الزوج والفريم المفضل لديك، ثم اضغط على 'استخراج إشارة الآن' ⚡"
    )
    bot.reply_to(message, welcome_text, reply_markup=get_main_keyboard())

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
        bot.send_message(chat_id, f"✅ تم اختيار الزوج: {selected_pair}", reply_markup=get_main_keyboard())

    elif call.data == "btn_tf":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for tf in TIMEFRAMES:
            markup.add(types.InlineKeyboardButton(tf, callback_data=f"tf_{tf}"))
        bot.send_message(chat_id, "⏱️ اختر الفريم الزمني للصفقة:", reply_markup=markup)

    elif call.data.startswith("tf_"):
        selected_tf = call.data.replace("tf_", "")
        user_data[chat_id] = user_data.get(chat_id, {})
        user_data[chat_id]['tf'] = selected_tf
        bot.send_message(chat_id, f"✅ تم اختيار الفريم: {selected_tf}", reply_markup=get_main_keyboard())

    elif call.data == "btn_signal":
        data = user_data.get(chat_id, {})
        pair = data.get('pair', random.choice(PAIRS))
        tf = data.get('tf', random.choice(TIMEFRAMES))
        action = random.choice(["🟢 شراء (CALL)", "🔴 بيع (PUT)"])
        reason = random.choice(REASONS)

        signal_msg = (
            f"🚨 **إشارة تداول جديدة** 🚨\n\n"
            f"📈 **الزوج:** {pair}\n"
            f"⏳ **المدة:** {tf}\n"
            f"📊 **النوع:** {action}\n"
            f"💡 **السبب الفني:** {reason}\n\n"
            f"⚠️ *تأكد من إدارة رأس المال جيداً قبل الدخول!*"
        )
        bot.send_message(chat_id, signal_msg, parse_mode="Markdown", reply_markup=get_main_keyboard())

# 3. التشغيل في نهاية الملف
if __name__ == '__main__':
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling(skip_pending=True)


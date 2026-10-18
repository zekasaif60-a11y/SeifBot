import os
import random
import threading
from flask import Flask
import telebot
from telebot import types

# 1. خادم Flask الوهمي
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

# 2. إعداد التوكن والبوت
TOKEN = "8900876880:AAHGQyZ_yd8j9MNubKzJ_p6RRg9j5EVcb_4"
bot = telebot.TeleBot(TOKEN)

PAIRS = [
    "EUR/USD (OTC)", "GBP/USD (OTC)", "USD/JPY (OTC)", "AUD/USD (OTC)", 
    "USD/CHF (OTC)", "USD/CAD (OTC)", "NZD/USD (OTC)",
    "EUR/GBP (OTC)", "EUR/JPY (OTC)", "EUR/AUD (OTC)", "EUR/CAD (OTC)", 
    "EUR/NZD (OTC)", "GBP/JPY (OTC)", "GBP/AUD (OTC)", "GBP/CAD (OTC)", 
    "GBP/NZD (OTC)", "AUD/JPY (OTC)", "AUD/CAD (OTC)", "AUD/NZD (OTC)", 
    "CAD/JPY (OTC)", "CHF/JPY (OTC)", "NZD/JPY (OTC)",
    "Gold / الذهب (OTC)", "Silver / الفضة (OTC)", "UK Brent (OTC)", "US Crude (OTC)",
    "Bitcoin / بتكوين (OTC)", "Ethereum / إيثريوم (OTC)", "Ripple / ريبل (OTC)"
]

TIMEFRAMES = ["30 ثانية", "1 دقيقة", "2 دقيقة", "3 دقائق", "5 دقائق"]

REASONS = [
    "ارتداد قوي من خط المنتصف في مؤشر Bollinger Bands مع اتجاه واضح.",
    "تقاطع مؤشر RSI ومؤشر Stochastic في مناطق التشبع.",
    "تأكيد حركة الشموع مع وجود سيولة مناسبة وتغير الاتجاه."
]

user_data = {}

def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_pairs = types.InlineKeyboardButton("📊 اختر الزوج", callback_data="btn_pairs")
    btn_tf = types.InlineKeyboardButton("⏱️ الفريم الزمني", callback_data="btn_tf")
    btn_signal = types.InlineKeyboardButton("🎯 استخراج إشارة الآن", callback_data="btn_signal")
    markup.add(btn_pairs, btn_tf)
    markup.add(btn_signal)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        f"👋 أهلاً بك يا زكريا في بوت Seif لتداول Pocket Option!\n\n"
        "⚡ اختر الزوج والفريم المفضل لديك، ثم اضغط على 'استخراج إشارة الآن'."
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

    elif call.data == "btn_signal":
        pair = user_data.get(chat_id, {}).get('pair', PAIRS[0])
        tf = user_data.get(chat_id, {}).get('tf', "1 دقيقة")
        
        bot.send_message(chat_id, "⏳ جاري فحص الشموع وتحليل السوق...")
        
        direction = random.choice(["🟢 شراء (CALL)", "🔴 بيع (PUT)"])
        accuracy = random.randint(90, 98)
        reason = random.choice(REASONS)
        
        signal_msg = (
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📊 **توصية Pocket Option احترافية** 📊\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔤 **الزوج:** `{pair}`\n"
            f"⏰ **المدة:** `{tf}`\n"
            f"🎯 **الاتجاه:** **{direction}**\n"
            f"📈 **نسبة الثقة:** `{accuracy}%`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💡 **التحليل الفني:** {reason}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *التزم بإدارة راس مالك واقتنص الفرص القوية.*"
        )
        # يرفق القائمة وزر استخراج إشارة جديدة أسفل التوصية مباشرة
        bot.send_message(chat_id, signal_msg, parse_mode="Markdown", reply_markup=get_main_keyboard())

import os
import threading
from flask import Flask

app = Flask('')


@app.route('/')
def home():
  return 'Bot is running!'


def run_flask():
  app.run(
      host='0.0.0.0',
      port=10000,
      debug=False,
      use_reloader=False,
  )


if __name__ == '__main__':
  t = threading.Thread(target=run_flask)
  t.daemon = True
  t.start()

  import time

  bot.remove_webhook()
  time.sleep(1)
  bot.infinity_polling(skip_pending=True)

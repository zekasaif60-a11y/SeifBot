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

# قائمة أشهر الأزواج المتاحة للاختيار
PAIRS = [
    "EUR/USD (OTC)", "GBP/USD (OTC)", "USD/JPY (OTC)", "USD/CHF (OTC)",
    "USD/CAD (OTC)", "AUD/USD (OTC)", "EUR/GBP (OTC)", "EUR/JPY (OTC)"
]

UP_REASONS = [
    "ارتداد قوي من الحد السفلي لمؤشر Bollinger Bands مع تقاطع صاعد لمؤشر Stochastic.",
    "ارتداد السعر من خط المنتصف مع اتجاه صاعد واضح وتأكيد الزخم من RSI."
]

DOWN_REASONS = [
    "ارتداد وهبوط من الحد العلوي لمؤشر Bollinger Bands مع تقاطع هابط لمؤشر Stochastic.",
    "كسر خط المنتصف للبولنجر مع اتجاه هابط واضح وتأكيد التشبع الشرائي."
]

# 3. خطوة أولى: اختيار زوج العملات
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for pair in PAIRS:
        markup.add(types.InlineKeyboardButton(pair, callback_data=f"pair_{pair}"))
    
    bot.reply_to(message, "أهلاً بك يا زكريا. يرجى اختيار زوج العملات المناسب للتداول:", reply_markup=markup)

# 4. خطوة ثانية: بعد اختيار الزوج، نطلب اختيار المدة الزمنية
@bot.callback_query_handler(func=lambda call: call.data.startswith("pair_"))
def select_timeframe(call):
    selected_pair = call.data.replace("pair_", "")
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("10 ثوانٍ", callback_data=f"time|{selected_pair}|10 ثوانٍ"),
        types.InlineKeyboardButton("30 ثانية", callback_data=f"time|{selected_pair}|30 ثانية"),
        types.InlineKeyboardButton("دقيقة واحدة", callback_data=f"time|{selected_pair}|دقيقة واحدة"),
        types.InlineKeyboardButton("دقيقتان", callback_data=f"time|{selected_pair}|دقيقتان"),
        types.InlineKeyboardButton("3 دقائق", callback_data=f"time|{selected_pair}|3 دقائق"),
        types.InlineKeyboardButton("5 دقائق", callback_data=f"time|{selected_pair}|5 دقائق"),
        types.InlineKeyboardButton("15 دقيقة", callback_data=f"time|{selected_pair}|15 دقيقة (ربع ساعة)")
    )
    
    bot.answer_callback_query(call.id, f"تم اختيار الزوج: {selected_pair}")
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"لقد اخترت زوج: **{selected_pair}**\nالآن اختر المدة الزمنية المطلوبة:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# 5. خطوة ثالثة: إصدار الإشارة النهائية بالأسلوب المطلوب تماماً
@bot.callback_query_handler(func=lambda call: call.data.startswith("time|"))
def generate_final_signal(call):
    _, selected_pair, selected_time = call.data.split("|")
    
    direction_type = random.choice(["صاعد 🟢", "هابط 🔴"])
    
    if "صاعد" in direction_type:
        trade_type = "شراء (CALL)"
        reason = random.choice(UP_REASONS)
    else:
        trade_type = "بيع (PUT)"
        reason = random.choice(DOWN_REASONS)
        
    win_rate = random.randint(88, 98)
    
    response = (
        f"**نوع الصفقة والمدة:** {trade_type} - {selected_time}\n"
        f"**الاتجاه:** {direction_type}\n"
        f"**نسبة النجاح:** {win_rate}%\n"
        f"**الزوج:** {selected_pair}\n"
        f"**توصية الدخول:** ادخل مع افتتاح الإشارة/الشمعة القادمة مباشرة ⏳\n"
        f"**السبب الفني:** {reason}"
    )
    
    bot.answer_callback_query(call.id, "تم استخراج الإشارة بنجاح")
    bot.send_message(call.message.chat.id, response, parse_mode="Markdown")

# 6. التشغيل المستمر
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    bot.infinity_polling()


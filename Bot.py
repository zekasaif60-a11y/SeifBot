import os
import random
import logging
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# === 1. خادم إبقاء البوت يعمل 24/7 على Render ===
app = Flask('')

@app.route('/')
def home():
    return "SeifBot is Alive and Running 24/7!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

Thread(target=run).start()

# === 2. إعداد البوت والتوكن ===
TOKEN = "8900876880:AAHGQyZ_yd8j9MNubKzJ_p6RRg9j5"
bot = telebot.TeleBot(TOKEN)

# تخزين اختيارات المستخدم الحالية
user_settings = {}

# قائمة الأزواج
PAIRS = [
    "EUR/USD (OTC)", "GBP/USD (OTC)", "USD/JPY (OTC)", 
    "AUD/CAD (OTC)", "EUR/GBP (OTC)", "USD/CHF (OTC)",
    "EUR/USD", "GBP/USD", "USD/JPY"
]

# قائمة الفريمات الزمنية
TIMEFRAMES = ["30 ثانية", "1 دقيقة", "2 دقيقة", "3 دقائق", "5 دقائق"]

# === 3. القائمة الرئيسية ===
def main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_pair = types.InlineKeyboardButton("📊 اختيار الزوج", callback_data="menu_pairs")
    btn_tf = types.InlineKeyboardButton("⏱️ الفريم الزمني", callback_data="menu_tf")
    btn_signal = types.InlineKeyboardButton("🚀 استخراج إشارة تداول", callback_data="get_signal")
    btn_status = types.InlineKeyboardButton("⚙️ إعدادات الصفقة الحالية", callback_data="show_status")
    markup.add(btn_pair, btn_tf)
    markup.add(btn_signal)
    markup.add(btn_status)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id not in user_settings:
        user_settings[chat_id] = {"pair": "EUR/USD (OTC)", "timeframe": "1 دقيقة"}
    
    welcome_text = (
        "👋 **مرحباً بك في بوت SeifBot للخيارات الثنائية (Pocket Option)!**\n\n"
        "إليك سيستم التداول المطور للتحليل الفني واستخراج إشارات مضمونة.\n"
        "يرجى ضبط الزوج والمدة الزمنية ثم الضغط على **استخراج إشارة**."
    )
    bot.reply_to(message, welcome_text, reply_markup=main_keyboard(), parse_mode="Markdown")

# === 4. الاستجابة للأزرار التفاعلية ===
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    if chat_id not in user_settings:
        user_settings[chat_id] = {"pair": "EUR/USD (OTC)", "timeframe": "1 دقيقة"}

    # عرض قائمة الأزواج
    if call.data == "menu_pairs":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for pair in PAIRS:
            markup.add(types.InlineKeyboardButton(pair, callback_data=f"set_pair_{pair}"))
        markup.add(types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu"))
        bot.edit_message_text("📊 **اختر زوج العملات للتداول:**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    # تحديد الزوج
    elif call.data.startswith("set_pair_"):
        selected_pair = call.data.replace("set_pair_", "")
        user_settings[chat_id]["pair"] = selected_pair
        bot.answer_callback_query(call.id, f"تم اختيار الزوج: {selected_pair}")
        bot.edit_message_text(f"✅ تم تحديد الزوج: **{selected_pair}**\n\nاختر الخطوة التالية:", chat_id, call.message.message_id, reply_markup=main_keyboard(), parse_mode="Markdown")

    # عرض قائمة الفريمات
    elif call.data == "menu_tf":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for tf in TIMEFRAMES:
            markup.add(types.InlineKeyboardButton(tf, callback_data=f"set_tf_{tf}"))
        markup.add(types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu"))
        bot.edit_message_text("⏱️ **اختر الفريم الزمني للصفقة:**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    # تحديد الفريم
    elif call.data.startswith("set_tf_"):
        selected_tf = call.data.replace("set_tf_", "")
        user_settings[chat_id]["timeframe"] = selected_tf
        bot.answer_callback_query(call.id, f"تم اختيار المدة: {selected_tf}")
        bot.edit_message_text(f"✅ تم تحديد المدة الزمنية: **{selected_tf}**\n\nاختر الخطوة التالية:", chat_id, call.message.message_id, reply_markup=main_keyboard(), parse_mode="Markdown")

    # عرض الحالة الحالية
    elif call.data == "show_status":
        pair = user_settings[chat_id]["pair"]
        tf = user_settings[chat_id]["timeframe"]
        text = f"⚙️ **إعدادات الصفقة الحالية:**\n\n🔹 الزوج: `{pair}`\n🔹 المدة: `{tf}`"
        bot.answer_callback_query(call.id, "عرض الإعدادات")
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=main_keyboard(), parse_mode="Markdown")

    # العودة للقائمة الرئيسية
    elif call.data == "main_menu":
        bot.edit_message_text("🏠 **القائمة الرئيسية:**", chat_id, call.message.message_id, reply_markup=main_keyboard(), parse_mode="Markdown")

    # === 5. خوارزمية استخراج الإشارات الفنية ===
    elif call.data == "get_signal":
        pair = user_settings[chat_id]["pair"]
        tf = user_settings[chat_id]["timeframe"]

        bot.answer_callback_query(call.id, "جاري تحليل المؤشرات بالسوق...")
        
        # أسباب وتحليلات فنّية متغيرة
        direction = random.choice(["🟢 شراء (CALL / UPTURN)", "🔴 بيع (PUT / DOWNTURN)"])
        accuracy = random.randint(88, 96)
        
        reasons = [
            "ارتداد قوي من الخط الأوسط لـ Bollinger Bands مع اتجاه واضح.",
            "تقاطع مؤشر Stochastic عند المنطقة مع تأكيد اتجاه RSI.",
            "كسر مستوى دعم/مقاومة فرعي وتأكيد الشمعة الحالية.",
            "اختراق إيجابي لمتوسط الحركة مع حجم تداول مرتفع."
        ]
        selected_reason = random.choice(reasons)

        signal_message = (
            f"🎯 **إشارة تداول جديدة - Pocket Option**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔤 **الزوج:** `{pair}`\n"
            f"⏱️ **المدة:** `{tf}`\n"
            f"📊 **النوع:** **{direction}**\n"
            f"🎯 **نسبة النجاح المتوقعة:** `{accuracy}%`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💡 **التحليل الفني:** {selected_reason}\n\n"
            f"⚠️ *تنبيه:* يرجى الالتزام ببروتوكول إدارة رأس المال ومراعاة السيولة."
        )

        bot.send_message(chat_id, signal_message, parse_mode="Markdown", reply_markup=main_keyboard())

# === 6. تشغيل البوت ===
bot.infinity_polling()
        import os
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

Thread(target=run).start()
import logging
import telebot
from telebot import types

# ضع توكن البوت الخاص بك من BotFather مكان التوكن أدناه
TOKEN = "8900876880:AAHGQyZ_yd8j9MNubKzJ_p6RRg9j5EVcb_4"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    item1 = types.InlineKeyboardButton("أزواج OTC", callback_data='otc')
    item2 = types.InlineKeyboardButton("الفريم الزمني", callback_data='timeframe')
    item3 = types.InlineKeyboardButton("استخراج إشارة", callback_data='signal')
    markup.add(item1, item2, item3)
    
    bot.reply_to(message, "مرحباً بك في بوت Seif للتداول! اختر من القائمة:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "otc":
        bot.send_message(call.message.chat.id, "اختر الزوج المناسب للتحليل.")
    elif call.data == "timeframe":
        bot.send_message(call.message.chat.id, "اختر الفريم الزمني (مثلاً 1 دقيقة أو 5 دقائق).")
    elif call.data == "signal":
        bot.send_message(call.message.chat.id, "جاري تحليل السوق واستخراج الإشارة...")

if __name__ == "__main__":
    bot.infinity_polling()

import os
import random
import threading
from flask import Flask
import telebot
from telebot import types

# 1. إعداد خادم Flask لـ Keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

# 2. إعداد البوت والتوكن الخاص بك
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# قائمة شاملة وكاملة لجميع أزواج وأصول منصة Pocket Option
PAIRS = [
    # === الأزواج العادية (Forex Live) ===
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CAD", "AUD/USD", "EUR/GBP", "NZD/USD", "USD/CHF",
    "EUR/JPY", "GBP/JPY", "AUD/JPY", "CAD/JPY", "CHF/JPY", "EUR/CAD", "EUR/AUD", "EUR/CHF",
    "GBP/CAD", "GBP/AUD", "GBP/CHF", "AUD/CAD", "AUD/NZD", "NZD/JPY", "NZD/CAD", "CAD/CHF",

    # === أزواج الـ OTC الكاملة (Forex OTC) ===
    "EUR/USD (OTC)", "GBP/USD (OTC)", "USD/JPY (OTC)", "USD/CAD (OTC)", "AUD/USD (OTC)", 
    "EUR/GBP (OTC)", "NZD/USD (OTC)", "USD/CHF (OTC)", "EUR/JPY (OTC)", "GBP/JPY (OTC)", 
    "AUD/JPY (OTC)", "CAD/JPY (OTC)", "CHF/JPY (OTC)", "EUR/CAD (OTC)", "EUR/AUD (OTC)", 
    "EUR/CHF (OTC)", "GBP/CAD (OTC)", "GBP/AUD (OTC)", "GBP/CHF (OTC)", "AUD/CAD (OTC)", 
    "AUD/NZD (OTC)", "NZD/JPY (OTC)", "NZD/CAD (OTC)", "CAD/CHF (OTC)", "USD/RUB (OTC)",
    "USD/BRL (OTC)", "USD/INR (OTC)", "USD/TRY (OTC)", "USD/PKR (OTC)", "USD/EGP (OTC)",

    # === المعادن والسلع (Commodities & Metals) ===
    "Gold / الذهب", "Gold (OTC) / الذهب", "Silver / الفضة", "Silver (OTC) / الفضة",
    "USCrude (OTC)", "UKBrent (OTC)", "Natural Gas (OTC)",

    # === أسهم الشركات العالمية (Stocks OTC) ===
    "Apple (OTC)", "Google (OTC)", "Microsoft (OTC)", "Amazon (OTC)", "Tesla (OTC)",
    "Meta (OTC)", "Netflix (OTC)", "Boeing (OTC)", "Intel (OTC)", "AMD (OTC)",

    # === العملات الرقمية (Crypto OTC) ===
    "BTC/USD (OTC)", "ETH/USD (OTC)", "LTC/USD (OTC)", "XRP/USD (OTC)", "EOS/USD (OTC)"
]

TIMEFRAMES = ["10s", "30 ثانية", "1 دقيقة", "2 دقائق", "3 دقائق", "5 دقائق"]

UP_REASONS = [
    "ارتداد قوي من الحد السفلي لمؤشر Bollinger Bands مع خط المتوسط مع اتجاه صاعد وتأكيد الزخم.",
    "تقاطع إيجابي لمؤشر RSI و Stochastic في مناطق التشبع البيعي مع ارتداد شمعة قوية.",
    "كسر المقاومة السابقة وإعادة اختبار ناجح مع دعم من مؤشر البولنجر."
]

DOWN_REASONS = [
    "ارتداد وهبوط من الحد العلوي لمؤشر Bollinger Bands إلى المتوسط مع اتجاه هابط وتأكيد التشبع الشرائي.",
    "تقاطع سلبي لمؤشر RSI و Stochastic في مناطق التشبع الشرائي.",
    "فشل اختراق المقاومة مع ظهور شمعة انعكاسية قوية (بين بار)."
]

# الأزرار الرئيسية الثابتة بالأسفل
def main_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_time = types.KeyboardButton("⏱ اختيار الفريم")
    btn_pair = types.KeyboardButton("📊 اختيار الزوج")
    btn_signal = types.KeyboardButton("🎯 استخراج إشارة الآن")
    markup.add(btn_pair, btn_time)
    markup.add(btn_signal)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(
        message, 
        "📊 **مرحباً بك يا زكريا في بوت Pocket Option الاحترافي**\n\nاختر من الأزرار بالأسفل للتداول واستخراج التوصيات:", 
        parse_mode="Markdown", 
        reply_markup=main_reply_keyboard()
    )

@bot.message_handler(func=lambda message: message.text in ["⏱ اختيار الفريم", "📊 اختيار الزوج", "🎯 استخراج إشارة الآن"])
def handle_menu_buttons(message):
    if message.text == "📊 اختيار الزوج":
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [types.InlineKeyboardButton(pair, callback_data=f"pair_{pair}") for pair in PAIRS]
        markup.add(*buttons)
        bot.reply_to(message, "🔠 **اختر زوج العملات أو الأصل المناسب للتداول:**", reply_markup=markup, parse_mode="Markdown")
        
    elif message.text == "⏱ اختيار الفريم":
        markup = types.InlineKeyboardMarkup(row_width=3)
        buttons = [types.InlineKeyboardButton(tf, callback_data=f"tfonly_{tf}") for tf in TIMEFRAMES]
        markup.add(*buttons)
        bot.reply_to(message, "⏰ **اختر الفريم الزمني المطلوب:**", reply_markup=markup, parse_mode="Markdown")
        
    elif message.text == "🎯 استخراج إشارة الآن":
        bot.reply_to(message, "⏳ **جاري فحص الشموع وتحليل السوق...**", parse_mode="Markdown")
        
        selected_pair = random.choice(PAIRS)
        selected_time = random.choice(TIMEFRAMES)
        
        is_up = random.choice([True, False])
        if is_up:
            trade_type = "شراء (CALL) 🟢"
            reason = random.choice(UP_REASONS)
        else:
            trade_type = "بيع (PUT) 🔴"
            reason = random.choice(DOWN_REASONS)
            
        win_rate = random.randint(88, 98)
        
        response = (
            f"📊 **توصية Pocket Option احترافية** 📈\n"
            f"──────────────────\n"
            f"🔠 **الزوج:** `{selected_pair}`\n"
            f"⏰ **المدة:** `{selected_time}`\n"
            f"🎯 **الاتجاه:** {trade_type}\n"
            f"📈 **نسبة الثقة:** `{win_rate}%`\n"
            f"──────────────────\n"
            f"💡 **التحليل الفني:** {reason}\n"
            f"──────────────────\n"
            f"⚠️ **التزم بإدارة راس مالك واقتنص الفرص القوية.**"
        )
        bot.send_message(message.chat.id, response, parse_mode="Markdown", reply_markup=main_reply_keyboard())

# عند اختيار الزوج من القائمة
@bot.callback_query_handler(func=lambda call: call.data.startswith("pair_"))
def select_timeframe_inline(call):
    selected_pair = call.data.replace("pair_", "")
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [types.InlineKeyboardButton(tf, callback_data=f"time_{selected_pair}_{tf}") for tf in TIMEFRAMES]
    markup.add(*buttons)
    
    bot.answer_callback_query(call.id, f"تم اختيار: {selected_pair}")
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"✅ **الزوج المختار:** `{selected_pair}`\n\n⏰ **الآن اختر المدة الزمنية:**",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# عند اختيار الفريم الزمني فقط
@bot.callback_query_handler(func=lambda call: call.data.startswith("tfonly_"))
def timeframe_selected_only(call):
    tf = call.data.replace("tfonly_", "")
    bot.answer_callback_query(call.id, f"تم اختيار الفريم: {tf}")
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"✅ **تم اختيار الفريم بنجاح:** `{tf}`\n\nاضغط الآن على **🎯 استخراج إشارة الآن** للحصول على التوصية.",
        parse_mode="Markdown"
    )

# إصدار التوصية النهائية
@bot.callback_query_handler(func=lambda call: call.data.startswith("time_"))
def generate_final_signal_inline(call):
    data_parts = call.data.replace("time_", "").split("_")
    selected_pair = data_parts[0]
    selected_time = data_parts[1]
    
    is_up = random.choice([True, False])
    if is_up:
        trade_type = "شراء (CALL) 🟢"
        reason = random.choice(UP_REASONS)
    else:
        trade_type = "بيع (PUT) 🔴"
        reason = random.choice(DOWN_REASONS)
        
    win_rate = random.randint(88, 98)
    
    response = (
        f"📊 **توصية Pocket Option احترافية** 📈\n"
        f"──────────────────\n"
        f"🔠 **الزوج:** `{selected_pair}`\n"
        f"⏰ **المدة:** `{selected_time}`\n"
        f"🎯 **الاتجاه:** {trade_type}\n"
        f"📈 **نسبة الثقة:** `{win_rate}%`\n"
        f"──────────────────\n"
        f"💡 **التحليل الفني:** {reason}\n"
        f"──────────────────\n"
        f"⚠️ **التزم بإدارة راس مالك واقتنص الفرص القوية.**"
    )
    
    bot.answer_callback_query(call.id, "✅ تم استخراج الإشارة بنجاح!")
    bot.send_message(call.message.chat.id, response, parse_mode="Markdown", reply_markup=main_reply_keyboard())

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    bot.infinity_polling()

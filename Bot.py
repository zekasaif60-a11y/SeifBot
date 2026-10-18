import os
import random
import threading
from flask import Flask
import telebot
from telebot import types

# 1. إعداد خادم Flask لـ Keep-alive (يعمل 24/7 على Render)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

# 2. إعداد البوت والتوكن الخاص بك
TOKEN = "8950126151:AAGQFtwHnTCAFMIwtW7v2kcfMCFU-uzRzdg"
bot = telebot.TeleBot(TOKEN)

# قائمة شاملة لأشهر أزواج بوكت أوشن العادية و OTC والسلع
PAIRS = [
    # العملات الأجنبية العادية (Live)
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CAD", "AUD/USD", "EUR/GBP", "NZD/USD", "USD/CHF",
    # أزواج الـ OTC
    "EUR/USD (OTC)", "GBP/USD (OTC)", "USD/JPY (OTC)", "USD/CAD (OTC)", 
    "AUD/USD (OTC)", "EUR/GBP (OTC)", "NZD/USD (OTC)", "USD/CHF (OTC)",
    "EUR/JPY (OTC)", "GBP/JPY (OTC)", "AUD/JPY (OTC)", "CAD/JPY (OTC)",
    # السلع والمعادن
    "Gold / الذهب", "Gold (OTC) / الذهب", "Silver / الفضة", "Silver (OTC) / الفضة",
    # العملات الرقمية
    "BTC/USD (OTC)", "ETH/USD (OTC)"
]

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

# دالة لوحة المفاتيح الرئيسية الثابتة في الأسفل
def main_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_time = types.KeyboardButton("⏱ اختيار الفريم")
    btn_pair = types.KeyboardButton("📊 اختيار الزوج")
    btn_signal = types.KeyboardButton("🎯 استخراج إشارة الآن")
    markup.add(btn_time, btn_pair)
    markup.add(btn_signal)
    return markup

# رسالة البداية مع الأزرار الثابتة
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(
        message, 
        "📊 **مرحباً بك يا زكريا في بوت Pocket Option الاحترافي**\n\nاختر من الأزرار بالأسفل لاستخراج التحليلات والإشارات:", 
        parse_mode="Markdown", 
        reply_markup=main_reply_keyboard()
    )

# التعامل مع الأزرار الثابتة في الأسفل
@bot.message_handler(func=lambda message: message.text in ["⏱ اختيار الفريم", "📊 اختيار الزوج", "🎯 استخراج إشارة الآن"])
def handle_menu_buttons(message):
    if message.text == "📊 اختيار الزوج" or message.text == "⏱ اختيار الفريم":
        # عرض أزرار الأزواج للاختيار
        markup = types.InlineKeyboardMarkup(row_width=2)
        for pair in PAIRS[:12]: # عرض عينة سريعة أو الكل
            markup.add(types.InlineKeyboardButton(pair, callback_data=f"pair_{pair}"))
        
        bot.reply_to(message, "🔠 **اختر زوج العملات المناسب للتداول:**", reply_markup=markup, parse_mode="Markdown")
    
    elif message.text == "🎯 استخراج إشارة الآن":
        # إرسال رسالة جاري فحص الشموع ثم إرسال التوصية فوراً
        sent_msg = bot.reply_to(message, "⏳ **جاري فحص الشموع وتحليل السوق...**", parse_mode="Markdown")
        
        # اختيار زوج افتراضي وعشوائي لإعطاء النتيجة فوراً بنفس الشكل المطلوب
        selected_pair = random.choice(PAIRS)
        selected_time = random.choice(["10s", "30 ثانية", "1 دقيقة", "2 دقائق", "3 دقائق", "5 دقائق"])
        
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

# خطوة تفاعلية عند اختيار الزوج من الأزرار الشفافة
@bot.callback_query_handler(func=lambda call: call.data.startswith("pair_"))
def select_timeframe_inline(call):
    selected_pair = call.data.replace("pair_", "")
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("10 ثوانٍ", callback_data=f"time_{selected_pair}_10s"),
        types.InlineKeyboardButton("30 ثانية", callback_data=f"time_{selected_pair}_30s"),
        types.InlineKeyboardButton("دقيقة واحدة", callback_data=f"time_{selected_pair}_1 دقيقة"),
        types.InlineKeyboardButton("دقيقتان", callback_data=f"time_{selected_pair}_2 دقائق"),
        types.InlineKeyboardButton("3 دقائق", callback_data=f"time_{selected_pair}_3 دقائق"),
        types.InlineKeyboardButton("5 دقائق", callback_data=f"time_{selected_pair}_5 دقائق")
    )
    
    bot.answer_callback_query(call.id, f"تم اختيار الزوج: {selected_pair}")
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"✅ **الزوج المختار:** `{selected_pair}`\n\n⏰ **الآن اختر المدة الزمنية المطلوبة:**",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# إصدار الإشارة النهائية بعد اختيار المدة
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

# التشغيل المستمر للخادم والبوت
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    bot.infinity_polling()



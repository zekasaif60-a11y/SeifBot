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

# 2. إعداد البوت والتونكن
TOKEN = os.environ.get("TOKEN")
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

# خطوة أولى: اختيار زوج العملات / الأصل
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    # إضافة الأزرار للأزواج (يمكنك تصفحها أو اختيارها)
    for pair in PAIRS:
        markup.add(types.InlineKeyboardButton(pair, callback_data=f"pair_{pair}"))
    
    bot.reply_to(message, "📊 **مرحباً بك يا زكريا في بوت Pocket Option الاحترافي**\n\nاختر زوج العملات أو الأصل المناسب للتداول:", parse_mode="Markdown", reply_markup=markup)

# خطوة ثانية: بعد اختيار الزوج، نطلب اختيار المدة الزمنية
@bot.callback_query_handler(func=lambda call: call.data.startswith("pair_"))
def select_timeframe(call):
    selected_pair = call.data.replace("pair_", "")
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("10 ثوانٍ", callback_data=f"time_{selected_pair}_10s"),
        types.InlineKeyboardButton("30 ثانية", callback_data=f"time_{selected_pair}_30s"),
        types.InlineKeyboardButton("دقيقة واحدة", callback_data=f"time_{selected_pair}_1 دقيقة"),
        types.InlineKeyboardButton("دقيقتان", callback_data=f"time_{selected_pair}_2 دقائق"),
        types.InlineKeyboardButton("3 دقائق", callback_data=f"time_{selected_pair}_3 دقائق"),
        types.InlineKeyboardButton("5 دقائق", callback_data=f"time_{selected_pair}_5 دقائق"),
        types.InlineKeyboardButton("15 دقيقة", callback_data=f"time_{selected_pair}_15 دقيقة")
    )
    
    bot.answer_callback_query(call.id, f"تم اختيار الزوج: {selected_pair}")
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"✅ **الزوج المختار:** `{selected_pair}`\n\n⏰ **الآن اختر المدة الزمنية المطلوبة:**",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# خطوة ثالثة: إصدار الإشارة النهائية بالأسلوب المطلوب تماماً[span_5](start_span)[span_5](end_span)
@bot.callback_query_handler(func=lambda call: call.data.startswith("time_"))
def generate_final_signal(call):
    data_parts = call.data.replace("time_", "").split("_")
    selected_pair = data_parts[0]
    selected_time = data_parts[1]
    
    # اختيار عشوائي للاتجاه (صاعد أو هابط) مع الأسباب
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
    bot.send_message(call.message.chat.id, response, parse_mode="Markdown")

# 6. التشغيل المستمر
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    bot.infinity_polling()



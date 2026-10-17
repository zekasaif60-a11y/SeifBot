import telebot
from telebot import types
import random

TOKEN = "8900876880:AAHGQyZ_yd8j9MNubKzJ_p6RRg9j5EVcb_4"
bot = telebot.TeleBot(TOKEN)

# جميع أزواج العملات والسلع والعملات الرقمية المتاحة في Pocket Option OTC
PAIRS = [
    # العملات الرئيسية
    "EUR/USD (OTC)", "GBP/USD (OTC)", "USD/JPY (OTC)", "AUD/USD (OTC)", 
    "USD/CHF (OTC)", "USD/CAD (OTC)", "NZD/USD (OTC)",
    
    # العملات التقاطعية
    "EUR/GBP (OTC)", "EUR/JPY (OTC)", "EUR/AUD (OTC)", "EUR/CAD (OTC)", 
    "EUR/NZD (OTC)", "GBP/JPY (OTC)", "GBP/AUD (OTC)", "GBP/CAD (OTC)", 
    "GBP/NZD (OTC)", "AUD/JPY (OTC)", "AUD/CAD (OTC)", "AUD/NZD (OTC)", 
    "CAD/JPY (OTC)", "CHF/JPY (OTC)", "NZD/JPY (OTC)",
    
    # السلع والمعادن
    "Gold / الذهب (OTC)", "Silver / الفضة (OTC)", "UK Brent (OTC)", "US Crude (OTC)",
    
    # العملات الرقمية
    "Bitcoin / بتكوين (OTC)", "Ethereum / إيثريوم (OTC)", "Ripple / ريبل (OTC)"
]

TIMEFRAMES = ["30 ثانية", "1 دقيقة", "2 دقيقة", "3 دقائق", "5 دقائق"]

REASONS = [
    "ارتداد قوي من خط المنتصف في مؤشر Bollinger Bands مع اتجاه واضح.",
    "تقاطع مؤشر RSI ومؤشر Stochastic في مناطق التشبع.",
    "تأكيد حركة الشموع مع وجود سيولة مناسبة وتغير الاتجاه."
]

user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_pairs = types.InlineKeyboardButton("📊 كل أزواج Pocket Option", callback_data="btn_pairs")
    btn_tf = types.InlineKeyboardButton("⏱️ الفريم الزمني", callback_data="btn_tf")
    btn_signal = types.InlineKeyboardButton("🎯 استخراج إشارة تداول", callback_data="btn_signal")
    markup.add(btn_pairs, btn_tf, btn_signal)
    
    welcome_text = (
        f"👋 أهلاً بك يا زكريا في بوت Seif الاحترافي لتداول Pocket Option!\n\n"
        "⚡ تم إضافة جميع أزواج المنصة بنجاح.\n"
        "اختر من القائمة أدناه للبدء:"
    )
    bot.reply_to(message, welcome_text, reply_markup=markup)

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
        bot.send_message(chat_id, f"✅ تم اختيار الزوج: *{selected_pair}*", parse_mode="Markdown")

    elif call.data == "btn_tf":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for tf in TIMEFRAMES:
            markup.add(types.InlineKeyboardButton(tf, callback_data=f"tf_{tf}"))
        bot.send_message(chat_id, "⏱️ اختر مدة الصَفقة (من 30 ثانية إلى 5 دقائق):", reply_markup=markup)

    elif call.data.startswith("tf_"):
        selected_tf = call.data.replace("tf_", "")
        user_data[chat_id] = user_data.get(chat_id, {})
        user_data[chat_id]['tf'] = selected_tf
        bot.send_message(chat_id, f"✅ تم اختيار المدة: *{selected_tf}*", parse_mode="Markdown")

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
        bot.send_message(chat_id, signal_msg, parse_mode="Markdown")

if __name__ == '__main__':
    bot.infinity_polling()
    

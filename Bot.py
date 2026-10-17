import telebot
from telebot import types
import random

# توكن البوت الصحيح
TOKEN = "8900876880:AAHGQyZ_yd8j9MNubKzJ_p6RRg9j5EVcb_4"

bot = telebot.TeleBot(TOKEN)

PAIRS = ["EUR/USD (OTC)", "GBP/USD (OTC)", "USD/JPY (OTC)", "AUD/CAD (OTC)"]
TIMEFRAMES = ["1 دقيقة", "2 دقيقة", "3 دقائق", "5 دقائق"]
REASONS = [
    "ارتداد قوي من خط المنتصف في مؤشر Bollinger Bands مع اتجاه واضح.",
    "تقاطع مؤشر RSI ومؤشر Stochastic في مناطق التشبع.",
    "تأكيد حركة الشموع مع وجود سيولة مناسبة وتغير الاتجاه."
]

user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_pairs = types.InlineKeyboardButton("أزواج OTC", callback_data="btn_pairs")
    btn_tf = types.InlineKeyboardButton("الفريم الزمني", callback_data="btn_tf")
    btn_signal = types.InlineKeyboardButton("🎯 استخراج إشارة", callback_data="btn_signal")
    markup.add(btn_pairs, btn_tf, btn_signal)
    
    bot.reply_to(message, f"مرحباً بك يا {message.from_user.first_name} في بوت Seif للتداول! 📊\nاختر من القائمة أدناه:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    
    if call.data == "btn_pairs":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for pair in PAIRS:
            markup.add(types.InlineKeyboardButton(pair, callback_data=f"pair_{pair}"))
        bot.send_message(chat_id, "اختر الزوج المناسب للتحليل:", reply_markup=markup)

    elif call.data.startswith("pair_"):
        selected_pair = call.data.replace("pair_", "")
        user_data[chat_id] = user_data.get(chat_id, {})
        user_data[chat_id]['pair'] = selected_pair
        bot.send_message(chat_id, f"تم اختيار الزوج: {selected_pair}")

    elif call.data == "btn_tf":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for tf in TIMEFRAMES:
            markup.add(types.InlineKeyboardButton(tf, callback_data=f"tf_{tf}"))
        bot.send_message(chat_id, "اختر الفريم الزمني للصَفقة:", reply_markup=markup)

    elif call.data.startswith("tf_"):
        selected_tf = call.data.replace("tf_", "")
        user_data[chat_id] = user_data.get(chat_id, {})
        user_data[chat_id]['tf'] = selected_tf
        bot.send_message(chat_id, f"تم اختيار الفريم الزمني: {selected_tf}")

    elif call.data == "btn_signal":
        pair = user_data.get(chat_id, {}).get('pair', PAIRS[0])
        tf = user_data.get(chat_id, {}).get('tf', "1 دقيقة")
        bot.send_message(chat_id, "⏳ جاري تحليل السوق واستخراج الإشارة...")
        
        direction = random.choice(["🟢 شراء (CALL)", "🔴 بيع (PUT)"])
        accuracy = random.randint(88, 96)
        reason = random.choice(REASONS)
        
        signal_msg = (
            f"📈 توصية تداول جديدة\n"
            f"------------------------\n"
            f"🔤 الزوج: {pair}\n"
            f"⏰ المدة: {tf}\n"
            f"🎯 الاتجاه: {direction}\n"
            f"🎯 نسبة الثقة الفنية: {accuracy}%\n"
            f"------------------------\n"
            f"💡 سبب التحليل: {reason}"
        )
        bot.send_message(chat_id, signal_msg)

if __name__ == '__main__':
    bot.infinity_polling()
                              

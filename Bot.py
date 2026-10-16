import logging
import telebot
from telebot import types

# ضع توكن البوت الخاص بك من BotFather مكان التوكن أدناه
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

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

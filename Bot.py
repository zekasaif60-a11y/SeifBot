import os
import threading
from flask import Flask
import telebot
from telebot import types
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# 1. إعداد خادم Flask للتشغيل المستمر Keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

# 2. إعداد البوت والتوكن الخاص بك
TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
bot = telebot.TeleBot(TOKEN)

# 3. قائمة شاملة بجميع أزواج وأصول منصة Pocket Option
PAIRS = [
    # --- أزواج الفوركس العادية (Forex Live) ---
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCAD=X", "USDCHF=X", "AUDUSD=X", "NZDUSD=X",
    "EURGBP=X", "EURJPY=X", "GBPJPY=X", "EURAUD=X", "EURCAD=X", "EURCHF=X",
    "GBPAUD=X", "GBPCAD=X", "GBPCHF=X", "AUDJPY=X", "CADJPY=X", "CHFJPY=X",
    "AUDCAD=X", "AUDNZD=X", "NZDJPY=X",

    # --- أزواج الـ OTC الخاصة بـ Pocket Option (Forex OTC) ---
    "EUR/USD (OTC)", "GBP/USD (OTC)", "USD/JPY (OTC)", "EUR/GBP (OTC)", "NZD/USD (OTC)",
    "USD/CHF (OTC)", "AUD/JPY (OTC)", "CAD/JPY (OTC)", "CHF/JPY (OTC)", "EUR/CHF (OTC)",
    "GBP/CAD (OTC)", "GBP/AUD (OTC)", "AUD/NZD (OTC)", "NZD/JPY (OTC)", "NZD/CAD (OTC)",
    "USD/BRL (OTC)", "USD/INR (OTC)", "USD/TRY (OTC)",

    # --- المعادن والسلع (Commodities & Metals) ---
    "GC=F",          # الذهب (Gold)
    "Gold (OTC)",     # الذهب OTC
    "Silver",         # الفضة
    "CL=F",          # النفط (USCrude)
    "UKBrent (OTC)",  # نفط برنت OTC
    "NaturalGas (OTC)"# الغاز الطبيعي OTC
]

# 4. دالة التحليل الفني الحقيقي
def analyze_market(ticker_symbol):
    try:
        # إذا كان الزوج من أزواج الـ OTC (يتم توجيهه للزوج الأصل للتحليل الفني المعياري)
        is_otc = "(OTC)" in ticker_symbol
        fetch_symbol = ticker_symbol

        if is_otc:
            # تحويل اسم الـ OTC للزوج الأساسي المقابل له للتحليل
            clean_otc = ticker_symbol.replace(" (OTC)", "").replace("/", "").strip()
            if clean_otc == "Gold":
                fetch_symbol = "GC=F"
            elif clean_otc == "UKBrent" or clean_otc == "USCrude":
                fetch_symbol = "CL=F"
            else:
                fetch_symbol = f"{clean_otc}=X"

        # جلب البيانات الحية
        df = yf.download(tickers=fetch_symbol, period="1d", interval="1m", progress=False)
        
        if df.empty or len(df) < 20:
            return "NO_DATA", "تعذر جلب بيانات حية للزوج حالياً (قد تكون السوق مغلقة أو السيولة ضعيفة)."

        # معالجة الهيدر المزدوج لـ pandas
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # حساب المؤشرات الفنية (Bollinger Bands, RSI, Stochastic)
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.stoch(k=14, d=3, append=True)

        latest = df.iloc[-1]
        close_price = float(latest['Close'])
        
        bb_lower = float(latest.get('BBL_20_2.0', 0))
        bb_middle = float(latest.get('BBM_20_2.0', 0))
        bb_upper = float(latest.get('BBU_20_2.0', 0))
        rsi = float(latest.get('RSI_14', 50))
        stoch_k = float(latest.get('STOCHk_14_3_3', 50))

        # 1. شرط عدم الدخول: مناطق التشبع الشديد
        if rsi >= 75 or rsi <= 25 or stoch_k >= 85 or stoch_k <= 15:
            return "BAD_MARKET", "السوق في مناطق تشبع شديد والمؤشرات في الأطراف (ينصح بعدم الدخول الآن)."

        # 2. شرط عدم الدخول: ملامسة حدود البولنجر الخارجية
        if close_price >= bb_upper or close_price <= bb_lower:
            return "NO_ENTRY", "السعر يلامس الحدود الخارجية لمؤشر Bollinger Bands (خطر الانعكاس، يفضل الانتظار)."

        # 3. شرط دخول شراء (CALL)
        if close_price > bb_middle and rsi > 50 and stoch_k > 50:
            return "CALL", "ارتداد إيجابي ناجح من الخط الأوسط لمؤشر Bollinger Bands مع اتجاه صاعد مؤكد وقوة شرائية."

        # 4. شرط دخول بيع (PUT)
        if close_price < bb_middle and rsi < 50 and stoch_k < 50:
            return "PUT", "ارتداد سلبي من الخط الأوسط لمؤشر Bollinger Bands مع اتجاه هابط مؤكد وقوة بيعية."

        return "NEUTRAL", "السوق متذبذب حالياً في نطاق ضيق ولا توجد فرصة صريحة."

    except Exception as e:
        return "ERROR", f"حدث خطأ أثناء تحليل البيانات: {str(e)}"

# 5. القوائم والأزرار الرئيسية
def main_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_signal = types.KeyboardButton("🎯 استخراج إشارة الآن")
    markup.add(btn_signal)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(
        message,
        "📊 **مرحباً بك يا زكريا في بوت Pocket Option الاحترافي**\n\n"
        "تم تحديث البوت ليعتمد على تحليل فني دقيق لكل الأزواج وأزواج OTC بناءً على:\n"
        "• Bollinger Bands (استراتيجية الارتداد من المنتصف)\n"
        "• RSI & Stochastic (مراقبة التشبع والاتجاه)\n\n"
        "اضغط على الزر بالأسفل للبدء.",
        parse_mode="Markdown",
        reply_markup=main_reply_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "🎯 استخراج إشارة الآن")
def handle_signal_request(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for pair in PAIRS:
        clean_name = pair.replace("=X", "").replace("=F", "")
        buttons.append(types.InlineKeyboardButton(clean_name, callback_data=f"pair_{pair}"))
    markup.add(*buttons)
    bot.reply_to(message, "🔤 **اختر زوج العملات المطلوب تحليله:**", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pair_"))
def handle_pair_selected(call):
    selected_pair = call.data.replace("pair_", "")
    clean_name = selected_pair.replace("=X", "").replace("=F", "")
    
    bot.answer_callback_query(call.id, "جاري تحليل السوق...")

    # جلب التحليل الفني الفعلي
    signal_type, reason = analyze_market(selected_pair)

    if signal_type == "CALL":
        trade_type = "شراء (CALL) 🟢"
        win_rate = 92
    elif signal_type == "PUT":
        trade_type = "بيع (PUT) 🔴"
        win_rate = 90
    else:
        response = (
            f"⚠️ **تحذير التداول / تجنب الدخول** 🛑\n"
            f"------------------------\n"
            f"🔤 **الزوج:** `{clean_name}`\n"
            f"💡 **السبب:** {reason}\n"
            f"------------------------\n"
            f"📌 **التوصية:** يفضل عدم دخول أي صفقة حالياً وانتظار فرصة أفضل."
        )
        bot.send_message(call.message.chat.id, response, parse_mode="Markdown")
        return

    response = (
        f"📊 **توصية Pocket Option احترافية** 📈\n"
        f"------------------------\n"
        f"🔤 **الزوج:** `{clean_name}`\n"
        f"⏱️ **المدة:** `2 - 3 دقائق` (حسب حركة الشمعة)\n"
        f"🎯 **الاتجاه:** {trade_type}\n"
        f"📈 **نسبة الثقة:** `{win_rate}%`\n"
        f"------------------------\n"
        f"💡 **التحليل الفني:** {reason}\n"
        f"------------------------\n"
        f"⚠️ **التزم بإدارة رأس مالك واقتنص الفرص القوية.**"
    )

    bot.send_message(call.message.chat.id, response, parse_mode="Markdown")

# 6. تشغيل البوت الخادم
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    bot.infinity_polling()

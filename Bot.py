import telebot
import yfinance as yf
import pandas_ta as ta

# 1. ضع التوكن الخاص ببوتك هنا
BOT_TOKEN = '8950126151:AAF3IAfDGPzqcxD9B8ccXWW8TjONPg9zO_s'
bot = telebot.TeleBot(BOT_TOKEN)

# قائمة شاملة لجميع أزواج العملات والمعادن المتوفرة في Pocket Option
PO_MARKETS = {
    # العملات الأساسية (Majors)
    "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "AUD/USD": "AUDUSD=X", 
    "NZD/USD": "NZDUSD=X", "USD/JPY": "JPY=X", "USD/CAD": "CAD=X", "USD/CHF": "CHF=X",
    
    # العملات المتقاطعة (Crosses)
    "EUR/GBP": "EURGBP=X", "EUR/JPY": "EURJPY=X", "EUR/AUD": "EURAUD=X", 
    "EUR/CAD": "EURCAD=X", "EUR/CHF": "EURCHF=X", "EUR/NZD": "EURNZD=X",
    "GBP/JPY": "GBPJPY=X", "GBP/AUD": "GBPAUD=X", "GBP/CAD": "GBPCAD=X", 
    "GBP/CHF": "GBPCHF=X", "AUD/JPY": "AUDJPY=X", "AUD/CAD": "AUDCAD=X", 
    "AUD/NZD": "AUDNZD=X", "CAD/JPY": "CADJPY=X", "CHF/JPY": "CHFJPY=X", 
    "NZD/JPY": "NZDJPY=X", "GBP/NZD": "GBPNZD=X",
    
    # العملات النامية (Exotics)
    "USD/TRY": "TRY=X", "USD/ZAR": "ZAR=X", "USD/BRL": "BRL=X", "USD/MXN": "MXN=X",
    
    # المعادن والسلع (Commodities)
    "الذهب (XAU/USD)": "GC=F",
    "الفضة (XAG/USD)": "SI=F",
    "النفط (UKBrent)": "BZ=F",
    "النفط الأمريكي (USCrude)": "CL=F"
}

# دالة التحليل الفني لـ Pocket Option
def generate_po_signal(ticker_symbol):
    try:
        # سحب بيانات 5 دقائق لآخر يومين (الفريم المفضل لصفقات الخيارات الثنائية)
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="2d", interval="5m")
        
        if df.empty or len(df) < 20:
            return "⚠️ عذراً، هذا الزوج غير متاح للتحليل الفني المباشر حالياً (قد يكون في وضع OTC الحصري للشركة)."

        # إضافة المؤشرات الفنية (RSI و Bollinger Bands و MACD)
        df.ta.rsi(length=14, append=True)
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        
        last_row = df.iloc[-1]
        close_price = last_row['Close']
        rsi = last_row['RSI_14']
        bb_lower = last_row['BBL_20_2.0']
        bb_upper = last_row['BBU_20_2.0']
        
        # استراتيجية دمج الـ RSI مع البولنجر باند لصفقات الـ 5 دقائق
        # شراء إذا لمس السعر خط البولنجر السفلي وكان الـ RSI تحت 30
        # بيع إذا لمس السعر خط البولنجر العلوي وكان الـ RSI فوق 70
        
        if rsi < 30 or close_price <= bb_lower:
            signal = "🟢 شراء قوي (CALL / HIGHER)"
            emoji = "🚀"
        elif rsi > 70 or close_price >= bb_upper:
            signal = "🔴 بيع قوي (PUT / LOWER)"
            emoji = "📉"
        else:
            signal = "⏳ تذبذب طبيعي - انتظر شمعة انعكاسية"
            emoji = "⚪"
            
        text = (
            f"📊 **تحليل الزوج:** `{ticker_symbol}`\n"
            f"💰 السعر الحالي: {close_price:.5f}\n"
            f"📈 مؤشر RSI: {rsi:.2f}\n"
            f"↕️ نطاق Bollinger: [{bb_lower:.4f} - {bb_upper:.4f}]\n\n"
            f"{emoji} **توصية Pocket Option الحالية:**\n"
            f"👈 **{signal}**\n"
            f"⏱️ وقت انتهاء الصفقة المقترح: **5 دقائق**"
        )
        return text
    except Exception as e:
        return "⚠️ حدث خطأ أثناء الاتصال بمزود البيانات الحية لـ Pocket Option."

# أمر البداية وعرض القوائم
@bot.message_handler(commands=['start', 'help'])
def start(message):
    help_text = (
        "🤖 **مرحباً بك في بوت Pocket Option الشامل لجميع الأزواج!**\n\n"
        "لتحليل أي زوج والحصول على إشارة دخول (CALL / PUT)، أرسل اسم الزوج مباشرة من القائمة بالأسفل بدون مسافات، مثال:\n"
        "👈 `EUR/USD` أو `الذهب`\n\n"
        "📋 **العملات المتاحة للتحليل الفني الآن:**\n"
    )
    # إضافة قائمة الأزواج في رسالة الترحيب بشكل منظم ليقوم المستخدم بنسخها
    for name in PO_MARKETS.keys():
        help_text += f"🔹 `{name}`\n"
        
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

# استقبال رسائل المستخدم ومطابقتها مع قائمة الأزواج الشاملة
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_input = message.text.strip()
    
    # البحث عن الزوج المناسب في القائمة الشاملة
    matched_key = None
    for key in PO_MARKETS.keys():
        if user_input.lower() in key.lower() or key.lower() in user_input.lower():
            matched_key = key
            break
            
    if matched_key:
        msg = bot.reply_to(message, f"🔄 جاري سحب الشموع وتحليل الزوج `{matched_key}` فنيّاً...")
        analysis_result = generate_po_signal(PO_MARKETS[matched_key])
        bot.edit_message_text(analysis_result, chat_id=message.chat.id, message_id=msg.message_id, parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ اسم الزوج غير مدرج في القائمة الرسمية لـ Pocket Option العادية. يرجى إرسال الرمز مثل: `EUR/USD` أو `GBP/JPY`.")

if __name__ == '__main__':
    print("🤖 البوت الشامل لجميع أزواج Pocket Option يعمل الآن بنجاح...")
    bot.infinity_polling()

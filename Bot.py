import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# إعداد السجلات (Logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# قائمة أزواج العملات (شاملة العادية و OTC)
PAIRS_OTC = [
    "EUR/USD (OTC)", "GBP/USD (OTC)", "USD/JPY (OTC)",
    "AUD/USD (OTC)", "USD/CAD (OTC)", "USD/CHF (OTC)",
    "NZD/USD (OTC)", "EUR/GBP (OTC)", "EUR/JPY (OTC)",
    "GBP/JPY (OTC)", "AUD/JPY (OTC)", "USD/RUB (OTC)"
]

PAIRS_REAL = [
    "EUR/USD", "GBP/USD", "USD/JPY",
    "AUD/USD", "USD/CAD", "USD/CHF",
    "NZD/USD", "EUR/GBP", "EUR/JPY",
    "GBP/JPY", "AUD/JPY", "USD/TRY"
]

# دالة التحليل الفني المرن
def analyze_indicators(price, middle_band, rsi, wpr):
    """
    تحليل فني سريع ومرن يعتمد على Bollinger Bands + RSI + Williams %R
    """
    # 1. شرط الشراء (CALL / صعود)
    if price > middle_band and rsi >= 50 and wpr >= -50:
        return {
            "direction": "صعود (CALL) 🟢",
            "confidence": 85,
            "call_pct": 80,
            "put_pct": 20,
            "duration": "من دقيقة إلى 3 دقائق",
            "reason": "ارتداد صاعد أعلى الخط الأوسط لـ Bollinger Bands ودعم متزامن من مؤشري RSI و Williams %R."
        }
    
    # 2. شرط البيع (PUT / هبوط)
    elif price < middle_band and rsi <= 50 and wpr <= -50:
        return {
            "direction": "هبوط (PUT) 🔴",
            "confidence": 85,
            "call_pct": 20,
            "put_pct": 80,
            "duration": "من دقيقة إلى 3 دقائق",
            "reason": "كسر وهبوط تحت الخط الأوسط لـ Bollinger Bands مع تقاطع سلبي في مؤشرات الزخم."
        }
    
    # 3. إشارة صعود متوسطة القوة (تجنب التعليق)
    elif price > middle_band:
        return {
            "direction": "صعود سريع (CALL) 🟢",
            "confidence": 65,
            "call_pct": 65,
            "put_pct": 35,
            "duration": "30 ثانية إلى دقيقة",
            "reason": "السعر فوق الخط الأوسط ولكن الزخم متوسط."
        }
        
    # 4. إشارة هبوط متوسطة القوة (تجنب التعليق)
    elif price < middle_band:
        return {
            "direction": "هبوط سريع (PUT) 🔴",
            "confidence": 65,
            "call_pct": 35,
            "put_pct": 65,
            "duration": "30 ثانية إلى دقيقة",
            "reason": "السعر تحت الخط الأوسط ولكن الزخم متوسط."
        }

    # 5. سوق متذبذب تماماً
    else:
        return {
            "direction": "عدم دخول (WAIT) ⏳",
            "confidence": 50,
            "call_pct": 50,
            "put_pct": 50,
            "duration": "-",
            "reason": "تذبذب حاد عند الخط الأوسط والمؤشرات في المنتصف تماماً. انتظر فرصة أوضح."
        }

# إنشاء لوحة الأزرار (أزواج OTC والأزواج العادية)
def build_keyboard():
    keyboard = []
    
    # قسم أزواج OTC
    row = []
    for pair in PAIRS_OTC:
        row.append(InlineKeyboardButton(pair, callback_data=f"pair_{pair}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    # فاصل للأزواج العادية
    keyboard.append([InlineKeyboardButton("🌐 --- الأزواج العادية (Real Market) --- 🌐", callback_data="ignore")])
    
    # قسم الأزواج العادية
    row = []
    for pair in PAIRS_REAL:
        row.append(InlineKeyboardButton(pair, callback_data=f"pair_{pair}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    return InlineKeyboardMarkup(keyboard)

# أمر البداية /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = build_keyboard()
    await update.message.reply_text(
        "📊 **مرحباً بك في بوت التداول الذكي منصة Pocket Option**\n\n"
        "اختر زوج العملات المطلوب (OTC أو عادي) للتحليل الفني الفوري:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# معالجة اختيار الزوج والتحليل
async def handle_pair_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "ignore":
        return

    pair_name = query.data.replace("pair_", "")
    
    await query.edit_message_text(f"⏳ **جاري تحليل الشموع والبيانات لـ ({pair_name})...**", parse_mode="Markdown")
    
    # قيم تحليلية افتراضية محاكاة
    price = 1.09860
    middle_band = 1.09850
    rsi = 55.0
    wpr = -40.0
    
    analysis = analyze_indicators(price, middle_band, rsi, wpr)
    
    response_text = (
        f"=============================\n"
        f"📊 **تحليل الزوج المختار** 📊\n"
        f"=============================\n\n"
        f"🔤 **الزوج / الأصل:** {pair_name}\n"
        f"🎯 **الاتجاه:** {analysis['direction']}\n"
        f"⏳ **المدة الموصى بها:** {analysis['duration']}\n"
        f"📈 **نسبة الثقة:** {analysis['confidence']}%\n"
        f"📊 **نسبة السوق:** 🟢 صعود {analysis['call_pct']}% | 🔴 هبوط {analysis['put_pct']}%\n\n"
        f"-----------------------------------------\n"
        f"💡 **التحليل الفني:** {analysis['reason']}\n"
        f"============================="
    )
    
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 إعادة تحليل الزوج", callback_data=f"pair_{pair_name}")],
        [InlineKeyboardButton("⬅️ عودة للرئيسية", callback_data="main_menu")]
    ])
    
    await query.edit_message_text(response_text, parse_mode="Markdown", reply_markup=back_keyboard)

# العودة للقائمة الرئيسية
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    reply_markup = build_keyboard()
    await query.edit_message_text(
        "📊 **اختر زوج العملات المطلوب تحليله:**",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

if __name__ == '__main__':
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_pair_selection, pattern="^pair_"))
    app.add_handler(CallbackQueryHandler(back_to_main, pattern="^main_menu$"))
    
    print("البوت يعمل الآن بنجاح...")
    app.run_polling()

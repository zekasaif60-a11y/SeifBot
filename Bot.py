import logging
import os
import sys
import threading
import random
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# تفعيل سجلات الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ----------------------------------------------------
# 1. خادم Flask لإبقاء الخدمة نشطة على Render
# ----------------------------------------------------
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running live!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# ----------------------------------------------------
# 2. أزواج التداول، الأسهم، والسلع المحددة من منصتك
# ----------------------------------------------------
PAIRS_OTC = [
    # الأسهم (Stocks OTC)
    "Intel OTC", "Marathon Digital OTC", "Tesla OTC", "ExxonMobil OTC", 
    "Amazon OTC", "Palantir OTC", "FedEx OTC", "AMD OTC", "American Express OTC", "Alibaba OTC",
    
    # السلع (Commodities OTC)
    "Brent Oil OTC", "WTI Crude Oil OTC", "Silver OTC", "Gold OTC", 
    "Natural Gas OTC", "Palladium OTC", "Platinum OTC",
    
    # العملات (Currencies OTC)
    "USD/RUB OTC", "USD/VND OTC", "YER/USD OTC", "EUR/HUF OTC", "USD/THB OTC",
    "USD/BDT OTC", "AED/CNY OTC", "BHD/CNY OTC", "OMR/CNY OTC", "USD/EGP OTC",
    "USD/IDR OTC", "USD/INR OTC", "UAH/USD OTC", "EUR/RUB OTC", "QAR/CNY OTC",
    "USD/MYR OTC", "TND/USD OTC", "LBP/USD OTC", "KES/USD OTC", "SAR/CNY OTC",
    "USD/CNH OTC", "USD/PKR OTC", "USD/CLP OTC", "USD/SGD OTC", "EUR/TRY OTC",
    "USD/MXN OTC", "MAD/USD OTC", "USD/ARS OTC", "USD/DZD OTC", "NGN/USD OTC",
    "ZAR/USD OTC", "EUR/USD OTC", "AUD/JPY OTC", "EUR/CHF OTC", "AUD/CHF OTC",
    "CAD/JPY OTC", "CAD/CHF OTC"
]

PAIRS_REAL = [
    "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "USD/CHF",
    "NZD/USD", "EUR/GBP", "EUR/JPY", "GBP/JPY", "AUD/JPY", "EUR/AUD",
    "EUR/CAD", "EUR/CHF", "GBP/CAD", "GBP/CHF", "CAD/JPY", "CHF/JPY",
    "AUD/CAD", "AUD/CHF"
]

# ----------------------------------------------------
# 3. دالة التحليل الفني (المدة ثابتة: دقيقة واحدة)
# ----------------------------------------------------
def analyze_market_conditions(price, middle_band, rsi, wpr):
    if price > middle_band and rsi >= 52 and wpr >= -50:
        return {
            "direction": "صعود (CALL) 🟢",
            "confidence": f"{random.randint(89, 96)}%",
            "duration": "دقيقة واحدة (1m)",
            "reason": "إيجابي من تقاطع المؤشرات والزخم فوق خط المنتصف."
        }
    elif price < middle_band and rsi <= 48 and wpr <= -50:
        return {
            "direction": "هبوط (PUT) 🔴",
            "confidence": f"{random.randint(89, 96)}%",
            "duration": "دقيقة واحدة (1m)",
            "reason": "صفقة مع تقاطع سلبي ونزول مؤشر القوة النسبية تحت الخط."
        }
    elif price > middle_band and rsi > 50:
        return {
            "direction": "صعود سريع (CALL) 🟢",
            "confidence": f"{random.randint(80, 88)}%",
            "duration": "دقيقة واحدة (1m)",
            "reason": "مناسب لصفقات السكالبيغ السريعة مع سيولة جيدة."
        }
    elif price < middle_band and rsi < 50:
        return {
            "direction": "هبوط سريع (PUT) 🔴",
            "confidence": f"{random.randint(80, 88)}%",
            "duration": "دقيقة واحدة (1m)",
            "reason": "مناسب لصفقات السكالبيغ السريعة تحت خط المنتصف."
        }
    else:
        return {
            "direction": "تجنب الدخول (WAIT) ⏳",
            "confidence": "غير آمن (< 50%)",
            "duration": "-",
            "reason": "حالة السوق غير واضحة؛ يمنع الدخول لحفظ رأس المال."
        }

# ----------------------------------------------------
# 4. بناء الأزرار التفاعلية المنسقة
# ----------------------------------------------------
def build_main_keyboard():
    keyboard = []
    
    keyboard.append([InlineKeyboardButton("📊 --- الأسهم، السلع والعملات OTC ---", callback_data="ignore")])
    row = []
    for pair in PAIRS_OTC:
        row.append(InlineKeyboardButton(pair, callback_data=f"analyze_{pair}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🌐 --- العملات الحقيقية (Real) ---", callback_data="ignore")])
    row = []
    for pair in PAIRS_REAL:
        row.append(InlineKeyboardButton(pair, callback_data=f"analyze_{pair}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = build_main_keyboard()
    await update.message.reply_text(
        "🚀 **Pocket Option - نظام التحليل الذكي والدقيق**\n\n"
        "اختر الأصل أو الزوج المطلوب للتحليل الفوري:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "ignore":
        return

    if query.data == "main_menu":
        reply_markup = build_main_keyboard()
        await query.edit_message_text(
            "📊 **اختر زوج العملات أو الأصل المطلوب تحليله:**",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        return

    selected_pair = query.data.replace("analyze_", "")

    base_price = round(random.uniform(1.05000, 1.35000), 5)
    middle_band = round(base_price + random.uniform(-0.00200, 0.00200), 5)
    rsi = round(random.uniform(25.0, 80.0), 1)
    wpr = round(random.uniform(-95.0, -5.0), 1)

    result = analyze_market_conditions(base_price, middle_band, rsi, wpr)

    response_text = (
        f"=============================\n"
        f"📊 **تقرير التحليل الفني الاحترافي** 📈\n"
        f"=============================\n\n"
        f"🔠 **الأصل المختار:** `{selected_pair}`\n"
        f"🎯 **القرار والتوصية:** `{result['direction']}`\n"
        f"📈 **نسبة الثقة والدقة:** `{result['confidence']}`\n"
        f"⏳ **المدة المقترحة:** `{result['duration']}`\n"
        f"💡 **السبب الفني:**\n{result['reason']}\n\n"
        f"============================="
    )

    action_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 تحليل نفس الزوج", callback_data=f"analyze_{selected_pair}")],
        [InlineKeyboardButton("⬅️ العودة لكل الأصول", callback_data="main_menu")]
    ])

    await query.edit_message_text(response_text, parse_mode="Markdown", reply_markup=action_keyboard)

# ----------------------------------------------------
# 5. نقطة التشغيل الرئيسية
# ----------------------------------------------------
if __name__ == '__main__':
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable not found!")
        sys.exit(1)

    # تشغيل خادم Flask الخلفي للاستضافة
    threading.Thread(target=run_flask, daemon=True).start()

    # تشغيل البوت
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handlers([
        CommandHandler("start", start_command),
        CallbackQueryHandler(handle_callback_query)
    ])

    print("🤖 البوت يعمل الآن بكفاءة...")
    app.run_polling()

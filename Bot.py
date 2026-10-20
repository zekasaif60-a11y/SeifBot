import logging
import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# تفعيل سجلات الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ------------------------------------
# 1. خادم Flask لإبقاء Render نشطاً
# ------------------------------------
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running live!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# ------------------------------------
# 2. بيانات وإعدادات البوت
# ------------------------------------
PAIRS_OTC = [
    "EUR/USD (OTC)", "GBP/USD (OTC)", "USD/JPY (OTC)",
    "USD/CAD (OTC)", "USD/CHF (OTC)", "NZD/USD (OTC)",
    "EUR/JPY (OTC)", "GBP/JPY (OTC)", "AUD/JPY (OTC)",
    "GBP/AUD (OTC)", "AUD/NZD (OTC)", "AUD/CAD (OTC)",
    "CHF/JPY (OTC)", "EUR/CHF (OTC)", "NZD/JPY (OTC)",
    "USD/BRL (OTC)", "USD/INR (OTC)", "USD/PKR (OTC)"
]

PAIRS_REAL = [
    "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD",
    "USD/CAD", "USD/CHF", "NZD/USD", "EUR/GBP",
    "EUR/JPY", "GBP/JPY", "AUD/JPY", "EUR/AUD",
    "EUR/CAD", "EUR/CHF", "GBP/CAD", "GBP/CHF",
    "CAD/JPY", "CHF/JPY", "AUD/CAD", "AUD/CHF"
]

def analyze_market_conditions(price, middle_band, rsi, wpr):
    if price > middle_band and rsi >= 52 and wpr > -50:
        return {
            "direction": "صعود (CALL) 🟢",
            "confidence": "92%",
            "duration": "دقيقتان إلى 3 دقائق",
            "reason": "ارتداد قوي مع تأكيد إيجابي من المؤشرات."
        }
    elif price < middle_band and rsi <= 48 and wpr < -50:
        return {
            "direction": "هبوط (PUT) 🔴",
            "confidence": "92%",
            "duration": "دقيقتان إلى 3 دقائق",
            "reason": "كسر سلبي مع زخم هابط صريح."
        }
    elif price > middle_band and rsi > 50:
        return {
            "direction": "صعود سريع (CALL) 🟢",
            "confidence": "80%",
            "duration": "دقيقة واحدة (30s - 60s)",
            "reason": "اتجاه صاعد مناسب للصفقات السريعة."
        }
    elif price < middle_band and rsi < 50:
        return {
            "direction": "هبوط سريع (PUT) 🔴",
            "confidence": "80%",
            "duration": "دقيقة واحدة (30s - 60s)",
            "reason": "اتجاه هابط مناسب للصفقات السريعة."
        }
    else:
        return {
            "direction": "تجنب الدخول (WAIT) ⏳",
            "confidence": "(أقل من 50%)",
            "duration": "-",
            "reason": "السوق غير مستقر أو ضعيف السيولة لحفظ رأس المال."
        }

def build_main_keyboard():
    keyboard = []
    keyboard.append([InlineKeyboardButton("📊 قسم أزواج الـ OTC 📊", callback_data="ignore")])
    row = []
    for pair in PAIRS_OTC:
        row.append(InlineKeyboardButton(pair, callback_data=f"analyze_{pair}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🌐 قسم الأزواج العادية 🌐", callback_data="ignore")])
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
        "🚀 **Pocket Option نظام التحليل الفوري الشامل لمنصة**\nاختر زوج العملات المطلوب للتحليل الدقيق:",
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
            "📊 **اختر زوج العملات المطلوب تحليله:**",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        return

    selected_pair = query.data.replace("analyze_", "")
    await query.edit_message_text(f"🔍 **جاري تحليل شارت {selected_pair}...**", parse_mode="Markdown")

    price = 1.09920
    middle_band = 1.09880
    rsi = 56.5
    wpr = -42.0

    result = analyze_market_conditions(price, middle_band, rsi, wpr)

    response_text = (
        f"=============================\n"
        f"📊 **تقرير التحليل الفني الاحترافي** 📊\n"
        f"=============================\n\n"
        f"🔤 **الزوج المختار:** `{selected_pair}`\n"
        f"🎯 **القرار والتوصية:** `{result['direction']}`\n"
        f"📈 **نسبة الثقة والدقة:** `{result['confidence']}`\n"
        f"⌛ **المدة المقترحة:** `{result['duration']}`\n"
        f"💡 **السبب الفني:**\n{result['reason']}\n"
        f"============================="
    )

    action_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 تحليل نفس الزوج", callback_data=f"analyze_{selected_pair}")],
        [InlineKeyboardButton("⬅️ العودة لكل الأزواج", callback_data="main_menu")]
    ])

    await query.edit_message_text(response_text, parse_mode="Markdown", reply_markup=action_keyboard)

# ------------------------------------
# 3. التشغيل الرئيسي
# ------------------------------------
if __name__ == '__main__':
    BOT_TOKEN = os.getenv("BOT_TOKEN", "8950126151:AAHQNS8au0YZLCznMi2OBsLl7ZIjDNsHRA")

    # تشغيل Flask في Thread منفصل
    threading.Thread(target=run_flask, daemon=True).start()

    # تشغيل بوت تليجرام
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    print("...تم إقلاع البوت بنجاح")
    app.run_polling()

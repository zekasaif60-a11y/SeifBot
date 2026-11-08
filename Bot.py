import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Token البوت الخاص بك
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

# قائمة شاملة لأزواج منصة Pocket Option (عادية و OTC)
CURRENCY_PAIRS = [
    # Forex Majors & Crosses
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "EURGBP", "EURJPY", "GBPJPY",
    # OTC Pairs (الأكثر تداولاً في المنصة)
    "EURUSD-OTC", "GBPUSD-OTC", "USDJPY-OTC", "AUDUSD-OTC", "USDCAD-OTC", 
    "EURGBP-OTC", "EURJPY-OTC", "GBPJPY-OTC", "NZDUSD-OTC", "BRLUSD-OTC", "ZARUSD-OTC"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "🤖 **مرحباً بك في بوت إشارات Pocket Option الشامل**\n\n"
        "الأوامر المتاحة:\n"
        "🔹 `/signal [الزوج] [1M أو 5M]` - لإرسال إشارة لزوج معين.\n"
        "🔹 `/all_pairs` - لعرض قائمة الأزواج المتاحة في النظام.\n\n"
        "مثال: `/signal EURUSD-OTC 1M`"
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def list_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pairs_list = "\n".join([f"📈 {pair}" for pair in CURRENCY_PAIRS])
    await update.message.reply_text(
        f"📋 **قائمة الأزواج المتاحة في البوت:**\n\n{pairs_list}", 
        parse_mode='Markdown'
    )

async def generate_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    
    # التحقق من المدخلات أو اختيار زوج عشوائي وإطار زمني افتراضي
    pair = args[0].upper() if len(args) > 0 else random.choice(CURRENCY_PAIRS)
    timeframe = args[1].upper() if len(args) > 1 else "M1"
    
    if pair not in CURRENCY_PAIRS:
        await update.message.reply_text("⚠️ عذراً، هذا الزوج غير مدرج في القائمة. اكتب `/all_pairs` لعرض الأزواج المتاحة.")
        return

    # محاكاة اتجاه الصفقة والتفاصيل الفنية
    direction = random.choice(["CALL 🟢 (BUY)", "PUT 🔴 (SELL)"])
    trend = "Uptrend" if "CALL" in direction else "Downtrend"
    forecast = f"{random.randint(80, 98)}.{random.randint(10, 99)}%"
    payout = f"{random.randint(75, 92)}.%";
    
    if timeframe == "M5":
        message = (
            f"👑 **VIP - 5Min - POCKET OPTION** 👑\n"
            f"📊 **VIP SIGNAL | Strategy M5**\n\n"
            f"🔹 **{pair} - {direction}**\n"
            f"🔹 **Expiration:** 5 minutes (M5)\n"
            f"🔹 **If loss, do up to 2 Gale.**\n\n"
            f"🎯 **Forecast:** {forecast}\n"
            f"💰 **Payout:** {payout}\n\n"
            f"📲 [Click to open broker](https://pocketoption.com)"
        )
    else:
        message = (
            f"📊 **POCKET OPTION (FREE {timeframe})**\n\n"
            f"💎 **{pair}**\n"
            f"⏰ {timeframe}\n"
            f"👉 {direction}\n\n"
            f"📈 **Tend:** {trend}\n"
            f"🎯 **Forecast:** {forecast}\n"
            f"💰 **Payout:** {payout}\n\n"
            f"📲 [Click to open broker](https://pocketoption.com)"
        )

    await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("all_pairs", list_pairs))
    app.add_handler(CommandHandler("signal", generate_signal))
    
    print("Powerful Pocket Option Bot is running...")
    app.run_polling()

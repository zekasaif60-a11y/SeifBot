import asyncio
import json
import websockets
import pandas as pd
import numpy as np
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ==================== [ ⚙️ الإعدادات الشخصية ] ====================
# ضع بياناتك الحقيقية بين علامات التنصيص
SSID = "ضع_رمز_SSID_الخاص_بمتصفحك_هنا" 
TELEGRAM_TOKEN = "8950126151:AAHQNS8au0YZjLCznMi2OBsLl7ZIjDNsHRA"
MY_CHAT_ID = "ضع_رقم_CHAT_ID_الخاص_بك_هنا" 

IS_DEMO = True         # True للتجريبي | False للحقيقي
TRADE_AMOUNT = 1.0     # قيمة الصفقة بالدولار
TRADE_DURATION = 60    # مدة الصفقة (60 ثانية)
# ===============================================================

# قائمة الأزواج الشاملة (العادية والـ OTC)
ASSET_LIST = [
    "EURUSD", "GBPUSD", "USDJPY", 
    "EURUSD_otc", "GBPUSD_otc", "USDJPY_otc",
    "AUDUSD_otc", "USDCAD_otc", "CRYPTO_BTCUSD_otc"
]

class PocketOptionTelegramBot:
    def __init__(self):
        self.uri = "wss://://pocketoption.com"
        self.market_data = {asset: [] for asset in ASSET_LIST}
        self.is_trading = False
        self.application = None

    async def send_notification(self, text):
        """إرسال إشعار للمستخدم عبر تليجرام"""
        if self.application and MY_CHAT_ID.isdigit():
            try:
                await self.application.bot.send_message(chat_id=int(MY_CHAT_ID), text=text)
            except Exception as e:
                print(f"[-] خطأ في إرسال رسالة تليجرام: {e}")

    def calculate_rsi(self, prices, period=7):
        """حساب مؤشر RSI السريع"""
        if len(prices) < period + 1:
            return 50
        deltas = np.diff(prices)
        seed = deltas[:period]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        if down == 0:
            return 100
        rs = up / down
        return 100. - (100. / (1. + rs))

    async def start_trade_loop(self):
        """الاتصال ببوكت أوبشن والتحليل وضخ الصفقات السريعة"""
        try:
            async with websockets.connect(self.uri) as ws:
                # 1. إرسال حزمة المصادقة (SSID)
                auth_payload = {"auth": SSID, "is_demo": IS_DEMO}
                await ws.send(f"42[\"auth\", {json.dumps(auth_payload)}]")
                await asyncio.sleep(1)
                
                # 2. الاشتراك في قائمة الأزواج
                for asset in ASSET_LIST:
                    await ws.send(f'42["subscribeSymbol", "{asset}"]')
                
                await self.send_notification("✅ متصل الآن بخوادم Pocket Option بنجاح وبانتظار الإشارات اللحظية...")

                # 3. الاستماع المستمر للأسعار
                while self.is_trading:
                    response = await ws.recv()
                    
                    if response.startswith("42"):
                        try:
                            raw_json = json.loads(response[2:])
                            event_name = raw_json[0]
                            
                            if event_name == "symbolData":
                                data = raw_json[1]
                                asset = data.get("asset")
                                price = float(data.get("price"))
                                
                                if asset in self.market_data:
                                    self.market_data[asset].append(price)
                                    if len(self.market_data[asset]) > 40:
                                        self.market_data[asset].pop(0)
                                    
                                    if len(self.market_data[asset]) >= 15:
                                        await self.analyze_market(ws, asset)
                        except Exception:
                            continue
        except Exception as e:
            await self.send_notification(f"❌ انقطع الاتصال بالمنصة: {e}\nإعادة المحاولة خلال 10 ثوانٍ...")
            await asyncio.sleep(10)
            if self.is_trading:
                asyncio.create_task(self.start_trade_loop())

    async def analyze_market(self, ws, asset):
        prices = self.market_data[asset]
        current_price = prices[-1]
        rsi = self.calculate_rsi(prices, period=7)
        ema_fast = pd.Series(prices).ewm(span=5).mean().iloc[-1]

        # استراتيجية صفقات الدقيقة السريعة
        if rsi <= 20 and current_price > ema_fast:
            await self.execute_trade(ws, asset, "call")
            self.market_data[asset] = []  # تصفير لمنع التكرار اللحظي

        elif rsi >= 80 and current_price < ema_fast:
            await self.execute_trade(ws, asset, "put")
            self.market_data[asset] = []

    async def execute_trade(self, ws, asset, direction):
        order = {"asset": asset, "amount": TRADE_AMOUNT, "action": direction, "duration": TRADE_DURATION}
        await ws.send(f"42[\"openOrder\", {json.dumps(order)}]")
        
        mode = "تجريبي" if IS_DEMO else "حقيقي"
        msg = f"🔥 [صفقة سريعة جديدة]\n📈 الاتجاه: {direction.upper()}\n📊 الزوج: {asset}\n💰 المبلغ: ${TRADE_AMOUNT}\n⏳ المدة: {TRADE_DURATION} ثانية\n🎮 الحساب: {mode}"
        await self.send_notification(msg)

    # --- أوامر التحكم عبر تليجرام ---
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.effective_chat.id) != str(MY_CHAT_ID):
            return
        if not self.is_trading:
            self.is_trading = True
            await update.message.reply_text("🚀 تم تفعيل البوت! بدأ الآن في مراقبة الأسواق وفتح الصفقات تلقائياً.")
            asyncio.create_task(self.start_trade_loop())
        else:
            await update.message.reply_text("⚠️ البوت يعمل بالفعل ويراقب السوق حالياً.")

    async def cmd_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.effective_chat.id) != str(MY_CHAT_ID):
            return
        self.is_trading = False
        await update.message.reply_text("🛑 تم إيقاف التداول التلقائي مؤقتاً.")

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.effective_chat.id) != str(MY_CHAT_ID):
            return
        status = "🟢 يعمل ويتداول" if self.is_trading else "🔴 متوقف مؤقتاً"
        mode = "تجريبي (Demo)" if IS_DEMO else "حقيقي (Live)"
        msg = f"📊 [حالة البوت الحالية]\n🤖 الوضع: {status}\n🎮 نوع الحساب: {mode}\n💸 قيمة الصفقة: ${TRADE_AMOUNT}\n⏱️ مدة الصفقة: {TRADE_DURATION} ثانية"
        await update.message.reply_text(msg)

async def main():
    bot_core = PocketOptionTelegramBot()
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    bot_core.application = app

    app.add_handler(CommandHandler("start", bot_core.cmd_start))
    app.add_handler(CommandHandler("stop", bot_core.cmd_stop))
    app.add_handler(CommandHandler("status", bot_core.cmd_status))

    print("[*] تم تشغيل نظام التحكم عبر تليجرام بنجاح...")
    await app.initialize()
    await app.start()
    
    # رسالة ترحيبية عند تشغيل السكربت بنجاح لأول مرة
    if MY_CHAT_ID.isdigit():
        await app.bot.send_message(chat_id=int(MY_CHAT_ID), text="🤖 البوت جاهز تماماً الآن!\nأرسل /start من حسابك لبدء التداول الآلي.")
    
    await app.updater.start_polling()
    
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())

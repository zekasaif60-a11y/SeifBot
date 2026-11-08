import time
import requests
import pandas as pd
import yfinance as yf

# ==================== إعدادات تيليجرام ====================
# ضع هنا توكن البوت الذي تحصل عليه من BotFather
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
# ضع هنا معرف الشات الخاص بك (Chat ID)
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

def send_telegram_message(message):
    """إرسال الإشارة فوراً على التيليجرام"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload)
    except Exception as e:
        print(f"خطأ في إرسال التيليجرام: {e}")

# ==================== قائمة الأزواج (28 زوجاً) ====================
ALL_FOREX_PAIRS = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X", "USDCHF=X", "NZDUSD=X",
    "EURGBP=X", "EURJPY=X", "EURCAD=X", "EURAUD=X", "EURNZD=X", "EURCHF=X",
    "GBPJPY=X", "GBPCAD=X", "GBPAUD=X", "GBPNZD=X", "GBPCHF=X",
    "AUDJPY=X", "AUDCAD=X", "AUDNZD=X", "AUDCHF=X",
    "NZDJPY=X", "NZDCAD=X", "NZDCHF=X",
    "CADJPY=X", "CADCHF=X", "CHFJPY=X"
]

def analyze_and_notify():
    print("\n" + "="*50)
    print(" جاري مسح السوق وفحص الـ 28 زوجاً على فريم الدقيقة...")
    print("="*50)

    signals_count = 0
    for symbol in ALL_FOREX_PAIRS:
        try:
            df = yf.download(symbol, period="1d", interval="1m", progress=False)
            if df.empty or len(df) < 30:
                continue
                
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # 1. Bollinger Bands (20)
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['STD'] = df['Close'].rolling(window=20).std()
            df['Upper'] = df['MA20'] + (df['STD'] * 2)
            df['Lower'] = df['MA20'] - (df['STD'] * 2)

            # 2. RSI (14)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # 3. Stochastic (%K & %D)
            low_min = df['Low'].rolling(window=14).min()
            high_max = df['High'].rolling(window=14).max()
            df['Stoch_K'] = ((df['Close'] - low_min) / (high_max - low_min)) * 100
            df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()

            # جلب آخر شمعة
            close = df['Close'].iloc[-1]
            upper = df['Upper'].iloc[-1]
            lower = df['Lower'].iloc[-1]
            rsi = df['RSI'].iloc[-1]
            stoch_k = df['Stoch_K'].iloc[-1]
            stoch_d = df['Stoch_D'].iloc[-1]
            pair_name = symbol.replace("=X", "")

            # الشروط الصارمة للدخول (صفقات سريعة 2-3 دقائق)
            if close <= lower and rsi < 30 and stoch_k > stoch_d:
                msg = (
                    f"🚨 **فرصة صفقة صعود (شراء)** 🟢\n"
                    f"-----------------------------\n"
                    f"🔹 الزوج: `{pair_name}`\n"
                    f"⏱️ الفريم: دقيقة واحدة (صفقة 2-3 دقائق)\n"
                    f"📊 السعر: `{close:.5f}`\n"
                    f"📉 مؤشر RSI: `{rsi:.1f}` (تشبع بيعي)\n"
                    f"📈 مؤشر Stoch_K: `{stoch_k:.1f}`\n"
                    f"💡 الحالة: ارتداد مؤكد من الحد السفلي للبولنجر."
                )
                print(f"[تم رصد فرصة صعود لـ {pair_name}]")
                send_telegram_message(msg)
                signals_count += 1

            elif close >= upper and rsi > 70 and stoch_k < stoch_d:
                msg = (
                    f"🚨 **فرصة صفقة هبوط (بيع)** 🔴\n"
                    f"-----------------------------\n"
                    f"🔹 الزوج: `{pair_name}`\n"
                    f"⏱️ الفريم: دقيقة واحدة (صفقة 2-3 دقائق)\n"
                    f"📊 السعر: `{close:.5f}`\n"
                    f"📈 مؤشر RSI: `{rsi:.1f}` (تشبع شرائي)\n"
                    f"📉 مؤشر Stoch_K: `{stoch_k:.1f}`\n"
                    f"💡 الحالة: ارتداد مؤكد من الحد العلوي للبولنجر."
                )
                print(f"[تم رصد فرصة هبوط لـ {pair_name}]")
                send_telegram_message(msg)
                signals_count += 1

        except Exception as e:
            continue

    if signals_count == 0:
        print("⏳ جاري الفحص... لا توجد فرص مكتملة الشروط حالياً في السوق.")

if __name__ == "__main__":
    print("🤖 بوت التنبيهات يعمل الآن...")
    while True:
        analyze_and_notify()
        # يفحص السوق بالكامل كل دقيقة
        time.sleep(60)

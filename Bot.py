import json
import time
import re
import websocket
import threading
import requests

# ==================== إعدادات الحساب والربط ====================

# 1. رمز المصادقة لمنصة Pocket Option (تأكد من تجديده من المتصفح إذا انتهت الجلسة)
POCKET_OPTION_SSID = '42["auth",{"session":"YOUR_POCKET_OPTION_SESSION_TOKEN","isDemo":1,"uid":1234567,"platform":1}]'

# 2. بيانات بوت التليجرام الخاص بك (جلب الـ Token من BotFather)
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN_HERE'

# إعدادات حجم ونوع الصفقات الافتراضية
TRADE_AMOUNT = 10     # مبلغ الصفقة بالدولار
TRADE_DURATION = 60   # مدة الصفقة بالثواني (دقيقة واحدة)
IS_DEMO = 1           # 1 للحساب التجريبي و 0 للحساب الحقيقي

# متغير عالمي للاحتفاظ باتصال الـ WebSocket الخاص بالمنصة
pocket_ws = None

# ==================== قائمة أزواج منصه Pocket Option المبرمجة ====================
POCKET_OPTION_ASSETS = {
    # أزواج العملات الاصطناعية الأكثر ربحية (OTC)
    "EURUSD": "EURUSD_OTC",
    "GBPUSD": "GBPUSD_OTC",
    "USDJPY": "USDJPY_OTC",
    "AUDCAD": "AUDCAD_OTC",
    "USDCAD": "USDCAD_OTC",
    "EURGBP": "EURGBP_OTC",
    "EURJPY": "EURJPY_OTC",
    "NZDUSD": "NZDUSD_OTC",
    "AUDUSD": "AUDUSD_OTC",
    "GBPJPY": "GBPJPY_OTC",
    
    # أزواج العملات في السوق الحقيقي المباشر (Real Market)
    "EURUSD_REAL": "EURUSD",
    "GBPUSD_REAL": "GBPUSD",
    "USDJPY_REAL": "USDJPY",
    "AUDUSD_REAL": "AUDUSD",
    
    # العملات الرقمية وسوق السلع والأسهم (Crypto & Commodities)
    "BTCUSDT": "BTCUSDT_OTC",
    "ETHUSDT": "ETHUSDT_OTC",
    "GOLD": "XAUUSD_OTC",      # الذهب عبر الـ OTC
    "SILVER": "XAGUSD_OTC",    # الفضة عبر الـ OTC
}

# ==================== دالة معالجة وتنفيذ الصفقات ====================

def place_order(asset, action):
    global pocket_ws
    if pocket_ws and pocket_ws.sock and pocket_ws.sock.connected:
        trade_request = [
            "openOrder",
            {
                "asset": asset,
                "amount": TRADE_AMOUNT,
                "action": action.lower(),  # "call" للشراء أو "put" للبيع
                "time": TRADE_DURATION,
                "isDemo": IS_DEMO
            }
        ]
        # إرسال الأمر الفوري عبر الـ WebSocket
        pocket_ws.send('42' + json.dumps(trade_request))
        print(f"🚀 [POCKET OPTION] تم تنفيذ صفقة {action.upper()} على {asset} بنجاح بقيمة ${TRADE_AMOUNT}")
    else:
        print("⚠️ [POCKET OPTION] الاتصال بالمنصة مقطوع! لا يمكن تنفيذ الصفقة.")

# ==================== دالة قراءة وتفسير رسائل التليجرام ====================

def parse_telegram_message(text):
    text_upper = text.upper().replace("/", "").replace(" ", "").replace("-", "")
    
    matched_asset = None
    action = None
    
    # 1. البحث عن الزوج داخل نص الرسالة ومطابقته بالقائمة المبرمجة لدينا
    for short_name, full_name in POCKET_OPTION_ASSETS.items():
        if short_name in text_upper:
            # التحقق إذا كانت الرسالة تطلب السوق الحقيقي عمداً أو الافتراضي OTC
            if "REAL" in text_upper and f"{short_name}_REAL" in POCKET_OPTION_ASSETS:
                matched_asset = POCKET_OPTION_ASSETS[f"{short_name}_REAL"]
            else:
                matched_asset = full_name
            break
            
    # إذا لم نجد أياً من الأزواج المحددة، نقوم بمحاولة استخراج ديناميكية عامة
    if not matched_asset:
        dynamic_match = re.search(r'([A-Z]{6})', text_upper)
        if dynamic_match:
            base_asset = dynamic_match.group(0)
            matched_asset = f"{base_asset}_OTC" # تحويل تلقائي لصيغة OTC
        else:
            return None, None

    # 2. تحديد الاتجاه (شراء CALL أم بيع PUT)
    if any(word in text_upper for word in ["BUY", "CALL", "UP", "📈", "HIGHER"]):
        action = "call"
    elif any(word in text_upper for word in ["SELL", "PUT", "DOWN", "📉", "LOWER"]):
        action = "put"
        
    return matched_asset, action

def check_telegram_updates():
    last_update_id = 0
    url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/getUpdates"
    
    print("📡 [TELEGRAM] جاري الاستماع لقنوات البوت وقراءة إشارات التداول الحية...")
    
    while True:
        try:
            response = requests.get(url, params={"offset": last_update_id + 1, "timeout": 30}, timeout=35)
            data = response.json()
            
            if "result" in data:
                for update in data["result"]:
                    last_update_id = update["update_id"]
                    
                    if "message" in update and "text" in update["message"]:
                        msg_text = update["message"]["text"]
                        print(f"📥 [TELEGRAM] رسالة جديدة: {msg_text}")
                        
                        asset, action = parse_telegram_message(msg_text)
                        
                        if asset and action:
                            print(f"🎯 [ANALYSIS] تم رصد إشارة متوافقة: {asset} -> {action.upper()}")
                            place_order(asset, action)
                        else:
                            print("ℹ️ [ANALYSIS] الرسالة لا تطابق شروط صفقة صالحة لمنصة Pocket Option.")
                            
        except Exception as e:
            print(f"⚠️ [TELEGRAM] خطأ في جلب البيانات: {e}")
        time.sleep(1)

# ==================== إدارة اتصال الـ WebSocket للمنصة ====================

def on_open(ws):
    print("🔌 [POCKET OPTION] تم الاتصال بنجاح. جاري إرسال المصادقة...")
    ws.send(POCKET_OPTION_SSID)

def on_close(ws, close_status_code, close_msg):
    print("❌ [POCKET OPTION] تم قطع الاتصال. إعادة المحاولة بعد 5 ثوانٍ...")
    time.sleep(5)
    connect_pocket_option()

def connect_pocket_option():
    global pocket_ws
    ws_url = "wss://://pocketoption.com"
    pocket_ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_close=on_close)
    ws_thread = threading.Thread(target=pocket_ws.run_forever)
    ws_thread.daemon = True
    ws_thread.start()

# ==================== تشغيل النظام بالكامل ====================

if __name__ == "__main__":
    connect_pocket_option()
    time.sleep(3)
    check_telegram_updates()

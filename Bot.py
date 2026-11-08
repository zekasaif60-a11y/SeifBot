import os
import threading
import time
import pandas as pd
import telebot
import yfinance as yf
from flask import Flask

# ==================== إعدادات التليجرام (بالتوكن الجديد) ====================
TOKEN = "8950126151:AAEisKfh2D07mH2mnf2E-ISnT8Mt_cH7Gyk"
CHAT_ID = "1706853546"

bot = telebot.TeleBot(TOKEN)
app = Flask("")


@app.route("/")
def home():
  return "SeifBot is Active and Running 24/7!"


def run_web():
  app.run(host="0.0.0.0", port=8080)


# ==================== أزواج السوق (28 زوجاً) ====================
ALL_FOREX_PAIRS = [
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "AUDUSD=X",
    "USDCAD=X",
    "USDCHF=X",
    "NZDUSD=X",
    "EURGBP=X",
    "EURJPY=X",
    "EURCAD=X",
    "EURAUD=X",
    "EURNZD=X",
    "EURCHF=X",
    "GBPJPY=X",
    "GBPCAD=X",
    "GBPAUD=X",
    "GBPNZD=X",
    "GBPCHF=X",
    "AUDJPY=X",
    "AUDCAD=X",
    "AUDNZD=X",
    "AUDCHF=X",
    "NZDJPY=X",
    "NZDCAD=X",
    "NZDCHF=X",
    "CADJPY=X",
    "CADCHF=X",
    "CHFJPY=X",
]


def trading_bot_loop():
  print("🤖 بدأ تشغيل محرك تحليل السوق...")
  while True:
    try:
      for symbol in ALL_FOREX_PAIRS:
        df = yf.download(symbol, period="1d", interval="1m", progress=False)
        if df.empty or len(df) < 30:
          continue

        if isinstance(df.columns, pd.MultiIndex):
          df.columns = df.columns.get_level_values(0)

        # 1. Bollinger Bands (20)
        df["MA20"] = df["Close"].rolling(window=20).mean()
        df["STD"] = df["Close"].rolling(window=20).std()
        df["Upper"] = df["MA20"] + (df["STD"] * 2)
        df["Lower"] = df["MA20"] - (df["STD"] * 2)

        # 2. RSI (14)
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # 3. Stochastic (%K & %D)
        low_min = df["Low"].rolling(window=14).min()
        high_max = df["High"].rolling(window=14).max()
        df["Stoch_K"] = (
            (df["Close"] - low_min) / (high_max - low_min)
        ) * 100
        df["Stoch_D"] = df["Stoch_K"].rolling(window=3).mean()

        close = df["Close"].iloc[-1]
        upper = df["Upper"].iloc[-1]
        lower = df["Lower"].iloc[-1]
        rsi = df["RSI"].iloc[-1]
        stoch_k = df["Stoch_K"].iloc[-1]
        stoch_d = df["Stoch_D"].iloc[-1]
        pair_name = symbol.replace("=X", "")

        # الشروط الصارمة لصفقات (2-3 دقائق)
        if close <= lower and rsi < 30 and stoch_k > stoch_d:
          msg = (
              f"🟢 **فرصة صفقة صعود (شراء)**\n🔹 الزوج:"
              f" `{pair_name}`\n📊 السعر: `{close:.5f}`\n📉 RSI:"
              f" `{rsi:.1f}`"
          )
          bot.send_message(CHAT_ID, msg, parse_mode="Markdown")

        elif close >= upper and rsi > 70 and stoch_k < stoch_d:
          msg = (
              f"🔴 **فرصة صفقة هبوط (بيع)**\n🔹 الزوج:"
              f" `{pair_name}`\n📊 السعر: `{close:.5f}`\n📈 RSI:"
              f" `{rsi:.1f}`"
          )
          bot.send_message(CHAT_ID, msg, parse_mode="Markdown")

      time.sleep(60)  # الفحص كل دقيقة
    except Exception as e:
      print(f"خطأ: {e}")
      time.sleep(30)


if __name__ == "__main__":
  t = threading.Thread(target=trading_bot_loop)
  t.start()
  run_web()

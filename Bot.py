import os
import threading
import time
from flask import Flask
import telebot
from telebot import types
import yfinance as yf
import pandas as pd
import numpy as np

# ==========================================
# 1. إعداد خادم Flask للتشغيل المستمر (24/7)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "SeifBot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

# ==========================================
# 2. إعداد البوت وقائمة جميع الأزواج (Pocket Option)
# ==========================================
TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
bot = telebot.TeleBot(TOKEN)

PAIRS = {
    # أزواج الفوركس العادية
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "CAD=X",
    "USD/CHF": "CHF=X",
    "NZD/USD": "NZDUSD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "AUD/JPY": "AUDJPY=X",
    "EUR/AUD": "EURAUD=X",
    "EUR/CAD": "EURCAD=X",
    "EUR/CHF": "EURCHF=X",
    "GBP/CAD": "GBPCAD=X",
    "GBP/CHF": "GBPCHF=X",
    "GBP/AUD": "GBPAUD=X",
    "AUD/CAD": "AUDCAD=X",
    "AUD/CHF": "AUDCHF=X",
    "CAD/CHF": "CADCHF=X",
    "NZD/JPY": "NZDJPY=X",
    "NZD/CAD": "NZDCAD=X",

    # أزواج الـ OTC
    "EUR/USD (OTC)": "EURUSD=X",
    "GBP/USD (OTC)": "GBPUSD=X",
    "USD/JPY (OTC)": "JPY=X",
    "AUD/USD (OTC)": "AUDUSD=X",
    "USD/CAD (OTC)": "CAD=X",
    "USD/CHF (OTC)": "CHF=X",
    "NZD/USD (OTC)": "NZDUSD=X",
    "EUR/GBP (OTC)": "EURGBP=X",
    "EUR/JPY (OTC)": "EURJPY=X",
    "GBP/JPY (OTC)": "GBPJPY=X",
    "AUD/JPY (OTC)": "AUDJPY=X",
    "USD/RUB (OTC)": "USDRUB=X",
    "USD/TRY (OTC)": "USDTRY=X",
    "USD/BRL (OTC)": "USDBRL=X",
    "USD/INR

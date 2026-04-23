import requests
import schedule
import time
from datetime import datetime

# === SOZLAMALAR (Railway environment variables) ===

import os
TELEGRAM_TOKEN = os.environ.get(“TELEGRAM_TOKEN”)
CHAT_ID        = os.environ.get(“CHAT_ID”)
GROQ_API_KEY   = os.environ.get(“GROQ_API_KEY”)

SYMBOLS = [“BTCUSDT”, “ETHUSDT”]

def get_ticker(symbol):
r = requests.get(
f”https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}”,
timeout=10
)
d = r.json()
return {
“price”:      float(d[“lastPrice”]),
“change_pct”: float(d[“priceChangePercent”]),
“high”:       float(d[“highPrice”]),
“low”:        float(d[“lowPrice”]),
}

def get_candles(symbol):
r = requests.get(
f”https://api.binance.com/api/v3/klines?symbol={symbol}&interval=15m&limit=20”,
timeout=10
)
return [
{“o”: float(c[1]), “h”: float(c[2]), “l”: float(c[3]), “c”: float(c[4])}
for c in r.json()
]

def analyze(symbol, ticker, candles):
candle_text = “ | “.join(
f”O:{c[‘o’]:.0f} H:{c[‘h’]:.0f} L:{c[‘l’]:.0f} C:{c[‘c’]:.0f}”
for c in candles[-10:]
)
prompt = f””“Kripto texnik tahlil qiling.
Aktiv: {symbol} | Narx: ${ticker[‘price’]:,.2f} | 24s: {ticker[‘change_pct’]:+.2f}%
Yuqori: ${ticker[‘high’]:,.2f} | Past: ${ticker[‘low’]:,.2f}
Oxirgi 10 sham: {candle_text}

Aynan shu formatda javob bering:
📊 Trend: [ko’tarilish/tushish/yon]
🎯 Signal: [BUY/SELL/HOLD]
📍 Support: $… | Resistance: $…
⚠️ Xavf: [past/o’rta/yuqori]
💬 Izoh: [1 jumla]”””

```
r = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300,
    },
    timeout=30
)
return r.json()["choices"][0]["message"]["content"]
```

def send_telegram(msg):
requests.post(
f”https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage”,
json={“chat_id”: CHAT_ID, “text”: msg, “parse_mode”: “HTML”},
timeout=10
)

def run():
for symbol in SYMBOLS:
try:
ticker  = get_ticker(symbol)
candles = get_candles(symbol)
result  = analyze(symbol, ticker, candles)
now     = datetime.now().strftime(”%d.%m.%Y %H:%M”)
display = symbol.replace(“USDT”, “/USDT”)
msg = (
f”<b>📈 {display} — {now}</b>\n”
f”💰 <b>${ticker[‘price’]:,.2f}</b> ({ticker[‘change_pct’]:+.2f}%)\n\n”
f”{result}”
)
send_telegram(msg)
print(f”{symbol} ✅”)
time.sleep(2)
except Exception as e:
print(f”{symbol} xato: {e}”)

print(“🚀 Bot ishga tushdi!”)
run()
schedule.every(15).minutes.do(run)
while True:
schedule.run_pending()
time.sleep(30)

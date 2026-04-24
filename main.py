import os,requests,time
t=os.environ.get("TELEGRAM_TOKEN")
c=os.environ.get("CHAT_ID")
g=os.environ.get("GROQ_API_KEY")
while True:
 for s in ["BTCUSDT","ETHUSDT"]:
  d=requests.get("https://api.binance.com/api/v3/ticker/24hr",params={"symbol":s}).json()
  p=d["lastPrice"]
  ch=d["priceChangePercent"]
  requests.post(f"https://api.telegram.org/bot{t}/sendMessage",json={"chat_id":c,"text":s+" $"+p+" ("+ch+"%)"})
  time.sleep(2)
 time.sleep(900)

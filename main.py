import os,requests,time
t=os.environ.get("TELEGRAM_TOKEN")
c=os.environ.get("CHAT_ID")
while True:
 for s in ["BTCUSDT","ETHUSDT"]:
  try:
   b=requests.get("https://api.binance.com/api/v3/ticker/24hr",params={"symbol":s}).json()
   p=b["lastPrice"]
   ch=float(b["priceChangePercent"])
   if ch>2:sig="BUY 🟢"
   elif ch<-2:sig="SELL 🔴"
   else:sig="HOLD 🟡"
   msg=s+" $"+p+"\n24s: "+str(round(ch,2))+"%\nSignal: "+sig
   requests.post("https://api.telegram.org/bot"+t+"/sendMessage",json={"chat_id":c,"text":msg})
   time.sleep(2)
  except Exception as e:
   print(str(e))
 time.sleep(900)

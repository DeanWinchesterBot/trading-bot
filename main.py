import os,requests,time
t=os.environ.get("TELEGRAM_TOKEN")
c=os.environ.get("CHAT_ID")
g=os.environ.get("GROQ_API_KEY")
while True:
 for s in ["BTCUSDT","ETHUSDT"]:
  try:
   d=requests.get("https://min-api.cryptocompare.com/data/price",params={"fsym":s[:3],"tsyms":"USD"}).json()
   p=str(d.get("USD","N/A"))
   requests.post("https://api.telegram.org/bot"+t+"/sendMessage",json={"chat_id":c,"text":s+" $"+p})
   time.sleep(2)
  except Exception as e:
   print(str(e))
 time.sleep(900)

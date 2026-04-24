import os,requests,time
t=os.environ.get("TELEGRAM_TOKEN")
c=os.environ.get("CHAT_ID")
g=os.environ.get("GROQ_API_KEY")
def analyze(s,p,ch):
 r=requests.post("https://api.groq.com/openai/v1/chat/completions",headers={"Authorization":"Bearer "+g,"Content-Type":"application/json"},json={"model":"llama3-70b-8192","messages":[{"role":"user","content":s+" narxi $"+p+", 24s ozgarish "+ch+"%. Signal: BUY SELL yoki HOLD? Sababi? 3 qatorda javob ber."}],"max_tokens":200},timeout=30)
 return r.json()["choices"][0]["message"]["content"]
while True:
 for s in ["BTCUSDT","ETHUSDT"]:
  try:
   d=requests.get("https://min-api.cryptocompare.com/data/price",params={"fsym":s[:3],"tsyms":"USD"}).json()
   p=str(d.get("USD","N/A"))
   b=requests.get("https://api.binance.com/api/v3/ticker/24hr",params={"symbol":s}).json()
   ch=str(round(float(b.get("priceChangePercent",0)),2))
   ai=analyze(s,p,ch)
   msg=s+" $"+p+" ("+ch+"%)\n\n"+ai
   requests.post("https://api.telegram.org/bot"+t+"/sendMessage",json={"chat_id":c,"text":msg})
   time.sleep(3)
  except Exception as e:
   print(str(e))
 time.sleep(900)

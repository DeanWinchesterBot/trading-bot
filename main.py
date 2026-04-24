import os,requests,time
t=os.environ.get("TELEGRAM_TOKEN")
c=os.environ.get("CHAT_ID")
while True:
 try:
  d=requests.get("https://api.coingecko.com/api/v3/simple/price",params={"ids":"bitcoin,ethereum","vs_currencies":"usd","include_24hr_change":"true"},timeout=10).json()
  btc=d["bitcoin"]
  eth=d["ethereum"]
  bp=str(btc["usd"])
  bc=str(round(btc["usd_24h_change"],2))
  ep=str(eth["usd"])
  ec=str(round(eth["usd_24h_change"],2))
  if float(bc)>2:bs="BUY 🟢"
  elif float(bc)<-2:bs="SELL 🔴"
  else:bs="HOLD 🟡"
  if float(ec)>2:es="BUY 🟢"
  elif float(ec)<-2:es="SELL 🔴"
  else:es="HOLD 🟡"
  msg="BTC $"+bp+" ("+bc+"%)\nSignal: "+bs+"\n\nETH $"+ep+" ("+ec+"%)\nSignal: "+es
  requests.post("https://api.telegram.org/bot"+t+"/sendMessage",json={"chat_id":c,"text":msg})
 except Exception as e:
  print(str(e))
 time.sleep(900)

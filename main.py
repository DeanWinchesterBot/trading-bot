import os,requests,time,threading
t=os.environ.get("TELEGRAM_TOKEN")
c=os.environ.get("CHAT_ID")
running=True
offset=0
def rsi(p,n=14):
 g,l=[],[]
 for i in range(1,len(p)):
  d=p[i]-p[i-1];g.append(max(d,0));l.append(max(-d,0))
 ag=sum(g[-n:])/n;al=sum(l[-n:])/n
 return round(100 if al==0 else 100-100/(1+ag/al),1)
def ema(p,n):
 k=2/(n+1);e=p[0]
 for x in p[1:]:e=x*k+e*(1-k)
 return e
def sig(sym,name):
 d=requests.get("https://api.coingecko.com/api/v3/coins/"+sym+"/market_chart",params={"vs_currency":"usd","days":"2","interval":"hourly"},timeout=15).json()
 p=[x[1] for x in d["prices"]];pr=round(p[-1],2);r=rsi(p);m=round(ema(p,12)-ema(p,26),2);ch=round((p[-1]-p[-24])/p[-24]*100,2);hi=max(p[-24:]);lo=min(p[-24:]);f1=round(lo+(hi-lo)*0.382,2);f2=round(lo+(hi-lo)*0.618,2)
 sc=0
 if r<35:sc+=2
 elif r<45:sc+=1
 elif r>65:sc-=2
 elif r>55:sc-=1
 if m>0:sc+=1
 else:sc-=1
 if ch>1:sc+=1
 elif ch<-1:sc-=1
 if pr<f1:sc+=1
 elif pr>f2:sc-=1
 s="KUCHLI BUY 🟢🟢" if sc>=3 else "BUY 🟢" if sc>=1 else "KUCHLI SELL 🔴🔴" if sc<=-3 else "SELL 🔴" if sc<=-1 else "HOLD 🟡"
 return name+" $"+str(pr)+" ("+str(ch)+"%)\nRSI:"+str(r)+" MACD:"+str(m)+"\nFib:$"+str(f1)+"|$"+str(f2)+"\nSignal:"+s+" (ball:"+str(sc)+")"
def gold():
 d=requests.get("https://api.coingecko.com/api/v3/coins/tether-gold/market_chart",params={"vs_currency":"usd","days":"2","interval":"hourly"},timeout=15).json();p2=[x[1] for x in d["prices"]];pr=round(p2[-1],2);r=rsi(p2);m=round(ema(p2,12)-ema(p2,26),2);ch=round((p2[-1]-p2[-24])/p2[-24]*100,2);hi=max(p2[-24:]);lo=min(p2[-24:]);f1=round(lo+(hi-lo)*0.382,2);f2=round(lo+(hi-lo)*0.618,2)
 sc=0
 if r<35:sc+=2
 elif r<45:sc+=1
 elif r>65:sc-=2
 elif r>55:sc-=1
 if m>0:sc+=1
 else:sc-=1
 if ch>0.5:sc+=1
 elif ch<-0.5:sc-=1
 if pr<f1:sc+=1
 elif pr>f2:sc-=1
 s="KUCHLI BUY 🟢🟢" if sc>=3 else "BUY 🟢" if sc>=1 else "KUCHLI SELL 🔴🔴" if sc<=-3 else "SELL 🔴" if sc<=-1 else "HOLD 🟡"
 return "XAUUSD $"+str(pr)+" ("+str(ch)+"%)\nRSI:"+str(r)+" MACD:"+str(m)+"\nFib:$"+str(f1)+"|$"+str(f2)+"\nSignal:"+s+" (ball:"+str(sc)+")"
def send(msg):
 requests.post("https://api.telegram.org/bot"+t+"/sendMessage",json={"chat_id":c,"text":msg},timeout=10)
def analyze():
 try:
  msg=sig("bitcoin","BTC")+"\n\n"+sig("ethereum","ETH")+"\n\n"+gold()
  send(msg)
 except Exception as e:
  print(str(e))
from commands import handle_command,send
def check_commands():
 global running,offset
 while True:
  try:
   r=requests.get("https://api.telegram.org/bot"+t+"/getUpdates",params={"offset":offset,"timeout":10},timeout=15).json()
   for u in r.get("result",[]):
    offset=u["update_id"]+1
    txt=u.get("message",{}).get("text","")
    result=handle_command(txt,t,c,g,analyze)
    if result=="start":
     running=True
     send(t,c,"✅ Bot ishga tushdi!")
     analyze()
    elif result=="stop":
     running=False
     send(t,c,"⛔ Bot toxtatildi. /start bilan qayta boshlang.")
  except Exception as e:
   print(str(e))
  time.sleep(3)
 while True:
  try:
   r=requests.get("https://api.telegram.org/bot"+t+"/getUpdates",params={"offset":offset,"timeout":10},timeout=15).json()
   for u in r.get("result",[]):
    offset=u["update_id"]+1
    txt=u.get("message",{}).get("text","")
    if txt=="/start":
     running=True
     send("✅ Bot ishga tushdi! Har 15 daqiqada signal keladi.")
     analyze()
    elif txt=="/stop":
     running=False
     send("⛔ Bot to'xtatildi. Qayta boshlash uchun /start yuboring.")
    elif txt=="/signal":
     send("⏳ Tahlil qilinmoqda...")
     analyze()
    elif txt=="/news":
     send("⏳ Yangiliklar qidirilmoqda...")
     try:
      import datetime
      today=datetime.datetime.now().strftime("%Y-%m-%d")
      news_prompt="Bugun "+today+" oltinga (XAUUSD) ta'sir qiladigan eng muhim 5 ta yangilikni qisqa va aniq yoz. Har birini emoji bilan boshla. Format: [emoji] [yangilik] -> [oltin uchun ta'siri: BULLISH/BEARISH/NEYTRAL]"
      r=requests.post("https://api.groq.com/openai/v1/chat/completions",headers={"Authorization":"Bearer "+g,"Content-Type":"application/json"},json={"model":"llama3-70b-8192","messages":[{"role":"user","content":news_prompt}],"max_tokens":500},timeout=30)
      news_text=r.json()["choices"][0]["message"]["content"]
      send("📰 XAUUSD YANGILIKLAR\n\n"+news_text+"\n\n⚠️ Bu AI tahlili, real yangilik emas!")
     except Exception as e:
      send("❌ Xato: "+str(e))

  except Exception as e:
   print(str(e))
  time.sleep(3)
def signal_loop():
 while True:
  if running:
   analyze()
  time.sleep(900)
threading.Thread(target=check_commands,daemon=True).start()
send("🤖 Bot ishga tushdi!\n/start - boshlash\n/stop - to'xtatish\n/signal - hozir signal")
signal_loop()

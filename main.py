import os,requests,time,threading,datetime
from flask import Flask,jsonify
HTML="""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Trade Signals</title><script src="https://telegram.org/js/telegram-web-app.js"></script><style>*{margin:0;padding:0;box-sizing:border-box}body{background:#1a1a2e;color:#fff;font-family:sans-serif;padding:16px}.header{text-align:center;padding:16px 0;margin-bottom:16px}.header h1{font-size:20px;color:#00d4aa}.card{background:#16213e;border-radius:12px;padding:16px;margin-bottom:12px;border:1px solid #0f3460}.price{font-size:22px;font-weight:bold}.change.up{color:#00d4aa}.change.down{color:#ff4757}.signal{display:inline-block;padding:6px 16px;border-radius:20px;font-size:14px;font-weight:bold;margin-top:10px}.signal.buy{background:#00d4aa22;color:#00d4aa;border:1px solid #00d4aa}.signal.sell{background:#ff475722;color:#ff4757;border:1px solid #ff4757}.signal.hold{background:#ffa50222;color:#ffa502;border:1px solid #ffa502}.ind{display:inline-block;background:#0f3460;border-radius:8px;padding:4px 10px;font-size:12px;margin:4px 4px 0 0}.ind span{color:#00d4aa;font-weight:bold}.tabs{display:flex;margin-bottom:16px;background:#16213e;border-radius:10px;padding:4px}.tab{flex:1;text-align:center;padding:10px;border-radius:8px;cursor:pointer;font-size:14px;color:#888}.tab.active{background:#0f3460;color:#fff}.news-item{background:#16213e;border-radius:10px;padding:14px;margin-bottom:10px;border-left:3px solid #00d4aa;font-size:13px;line-height:1.5}.news-item.bearish{border-left-color:#ff4757}.news-item.neutral{border-left-color:#ffa502}.btn{width:100%;padding:14px;background:#00d4aa;color:#000;border:none;border-radius:10px;font-size:15px;font-weight:bold;cursor:pointer;margin-top:8px}.loading{text-align:center;color:#888;padding:30px}</style></head><body><div class="header"><h1>📈 Trade Signals</h1><div id="time" style="font-size:12px;color:#888;margin-top:4px"></div></div><div class="tabs"><div class="tab active" id="tab1" onclick="showTab('signals')">📊 Signallar</div><div class="tab" id="tab2" onclick="showTab('news')">📰 Yangiliklar</div></div><div id="signals-tab"><div id="sc"><div class="loading">⏳ Yuklanmoqda...</div></div><button class="btn" onclick="loadSignals()">🔄 Yangilash</button></div><div id="news-tab" style="display:none"><div id="nc"><div class="loading">⏳ Yuklanmoqda...</div></div><button class="btn" onclick="loadNews()">🔄 Yangiliklar</button></div><script>const tg=window.Telegram.WebApp;tg.ready();tg.expand();function showTab(tab){document.getElementById("tab1").className="tab"+(tab=="signals"?" active":"");document.getElementById("tab2").className="tab"+(tab=="news"?" active":"");document.getElementById("signals-tab").style.display=tab=="signals"?"block":"none";document.getElementById("news-tab").style.display=tab=="news"?"block":"none";if(tab=="news")loadNews();}function sc(s){return s.includes("BUY")?"buy":s.includes("SELL")?"sell":"hold";}async function loadSignals(){document.getElementById("sc").innerHTML='<div class="loading">⏳...</div>';try{const r=await fetch("/api/signals");const d=await r.json();let h="";[["BTC","btc"],["ETH","eth"],["XAUUSD","gold"]].forEach(([n,k])=>{const i=d[k];if(!i||!i.price)return;const ch=parseFloat(i.change||0);h+=`<div class="card"><div style="font-size:13px;color:#888">${n}</div><div><span class="price">$${i.price}</span><span class="change ${ch>=0?"up":"down"}" style="font-size:13px;margin-left:8px">${ch>=0?"+":""}${ch}%</span></div><div style="margin-top:8px"><span class="ind">RSI <span>${i.rsi||"-"}</span></span><span class="ind">MACD <span>${i.macd||"-"}</span></span><span class="ind">Ball <span>${i.score||0}</span></span></div><div><span class="signal ${sc(i.signal||"HOLD")}">${i.signal||"HOLD"}</span></div></div>`;});document.getElementById("sc").innerHTML=h||'<div class="loading">Maʼlumot yoʼq</div>';document.getElementById("time").textContent="Yangilandi: "+new Date().toLocaleTimeString();}catch(e){document.getElementById("sc").innerHTML='<div class="loading">❌ Xato</div>';}}async function loadNews(){document.getElementById("nc").innerHTML='<div class="loading">⏳ AI tahlil qilmoqda...</div>';try{const r=await fetch("/api/news");const d=await r.json();const lines=d.news.split("\\n").filter(l=>l.trim());let h="";lines.forEach(l=>{const c=l.includes("BEARISH")?"bearish":l.includes("NEYTRAL")?"neutral":"";h+=`<div class="news-item ${c}">${l}</div>`;});document.getElementById("nc").innerHTML=h;}catch(e){document.getElementById("nc").innerHTML='<div class="loading">❌ Xato</div>';}}loadSignals();</script></body></html>"""
from flask_cors import CORS
app=Flask(__name__)
CORS(app)
t=os.environ.get("TELEGRAM_TOKEN")
c=os.environ.get("CHAT_ID")
g=os.environ.get("GROQ_API_KEY")
running=True
offset=0
def rsi(p,n=14):
 g2,l=[],[]
 for i in range(1,len(p)):
  d=p[i]-p[i-1];g2.append(max(d,0));l.append(max(-d,0))
 ag=sum(g2[-n:])/n;al=sum(l[-n:])/n
 return round(100 if al==0 else 100-100/(1+ag/al),1)
def ema(p,n):
 k=2/(n+1);e=p[0]
 for x in p[1:]:e=x*k+e*(1-k)
 return e
def send(msg):
 requests.post("https://api.telegram.org/bot"+t+"/sendMessage",json={"chat_id":c,"text":msg},timeout=10)
def sig(sym,name):
 d=requests.get("https://api.coingecko.com/api/v3/coins/"+sym+"/market_chart",params={"vs_currency":"usd","days":"2","interval":"hourly"},timeout=15).json()
 p=[x[1] for x in d["prices"]];pr=round(p[-1],2);r=rsi(p);m=round(ema(p,12)-ema(p,26),2);ch=round((p[-1]-p[-24])/p[-24]*100,2);hi=max(p[-24:]);lo=min(p[-24:]);f1=round(lo+(hi-lo)*0.382,2);f2=round(lo+(hi-lo)*0.618,2)
 sc=0
 if r<35:sc+=2
 elif r<45:sc+=1
 elif r>65:sc-=2
 elif r>55:sc-=1
 if ema(p,12)>ema(p,26):sc+=1
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
 if ema(p2,12)>ema(p2,26):sc+=1
 else:sc-=1
 if ch>0.5:sc+=1
 elif ch<-0.5:sc-=1
 if pr<f1:sc+=1
 elif pr>f2:sc-=1
 s="KUCHLI BUY 🟢🟢" if sc>=3 else "BUY 🟢" if sc>=1 else "KUCHLI SELL 🔴🔴" if sc<=-3 else "SELL 🔴" if sc<=-1 else "HOLD 🟡"
 return "XAUUSD $"+str(pr)+" ("+str(ch)+"%)\nRSI:"+str(r)+" MACD:"+str(m)+"\nFib:$"+str(f1)+"|$"+str(f2)+"\nSignal:"+s+" (ball:"+str(sc)+")"
def news():
 try:
  today=datetime.datetime.now().strftime("%Y-%m-%d")
  prompt="Bugun "+today+" oltinga (XAUUSD) ta'sir qiladigan eng muhim 5 ta yangilikni qisqa yoz. Har birini emoji bilan boshla. Format: [emoji] [yangilik] -> [BULLISH/BEARISH/NEYTRAL]"
  r=requests.post("https://api.groq.com/openai/v1/chat/completions",headers={"Authorization":"Bearer "+g,"Content-Type":"application/json"},json={"model":"llama3-70b-8192","messages":[{"role":"user","content":prompt}],"max_tokens":500},timeout=30)
  return r.json()["choices"][0]["message"]["content"]
 except Exception as e:
  return "Xato: "+str(e)
def analyze():
 try:
  msg=sig("bitcoin","BTC")+"\n\n"+sig("ethereum","ETH")+"\n\n"+gold()
  send(msg)
 except Exception as e:
  print(str(e))
def check_commands():
 global running,offset
 while True:
  try:
   r=requests.get("https://api.telegram.org/bot"+t+"/getUpdates",params={"offset":offset,"timeout":10},timeout=15).json()
   for u in r.get("result",[]):
    offset=u["update_id"]+1
    txt=u.get("message",{}).get("text","")
    if txt=="/start":
     running=True
     send("✅ Bot ishga tushdi!")
     analyze()
    elif txt=="/stop":
     running=False
     send("⛔ Bot toxtatildi. /start bilan qayta boshlang.")
    elif txt=="/signal":
     send("⏳ Tahlil qilinmoqda...")
     analyze()
    elif txt=="/news":
     send("⏳ Yangiliklar qidirilmoqda...")
     send("📰 XAUUSD YANGILIKLAR\n\n"+news()+"\n\n⚠️ Bu AI tahlili!")
    elif txt=="/help":
     send("📌 Buyruqlar:\n/start - Boshlash\n/stop - Toxtatish\n/signal - Hozir signal\n/news - Yangiliklar\n/help - Yordam")
  except Exception as e:
   print(str(e))
  time.sleep(3)
  last_data={"btc":{},"eth":{},"gold":{}}
@app.route("/api/signals")
def api_signals():
 return jsonify(last_data)
@app.route("/api/news")
def api_news():
 return jsonify({"news":news()})
@app.route("/")
def index():
 return HTML
def signal_loop():
 while True:
  if running:
   analyze()
  time.sleep(900)
threading.Thread(target=check_commands,daemon=True).start()
threading.Thread(target=signal_loop,daemon=True).start()
send("🤖 Bot ishga tushdi!")
app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

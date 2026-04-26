import os,requests,time,threading,datetime
from flask import Flask,jsonify
from flask_cors import CORS

# === SOZLAMALAR ===

t=os.environ.get("TELEGRAM_TOKEN","")
c=os.environ.get("CHAT_ID","")
g=os.environ.get("GROQ_API_KEY","")

app=Flask(**name**)
CORS(app)
running=True
offset=0
last_data={"btc":{},"eth":{},"gold":{}}

# === MATEMATIK FUNKSIYALAR ===

def ema(p,n):
k=2/(n+1);e=p[0]
for x in p[1:]:e=x*k+e*(1-k)
return round(e,4)

def rsi(p,n=14):
g2,l=[],[]
for i in range(1,len(p)):
d=p[i]-p[i-1];g2.append(max(d,0));l.append(max(-d,0))
ag=sum(g2[-n:])/n;al=sum(l[-n:])/n
return round(100 if al==0 else 100-100/(1+ag/al),1)

def macd_val(p):
return round(ema(p,12)-ema(p,26),4)

def bollinger(p,n=20):
s=p[-n:];m=sum(s)/n
std=(sum((x-m)**2 for x in s)/n)**0.5
return round(m-2*std,2),round(m,2),round(m+2*std,2)

def stoch_val(highs,lows,closes,n=14):
h=max(highs[-n:]);l=min(lows[-n:])
if h==l:return 50
return round((closes[-1]-l)/(h-l)*100,1)

def atr_val(highs,lows,closes,n=14):
trs=[]
for i in range(1,len(closes)):
tr=max(highs[i]-lows[i],abs(highs[i]-closes[i-1]),abs(lows[i]-closes[i-1]))
trs.append(tr)
return round(sum(trs[-n:])/n,2)

# === FIBONACCI BARCHA TURLARI ===

def fib_retracement(hi,lo):
r=hi-lo
return {
"0":round(hi,2),
"23.6":round(hi-r*0.236,2),
"38.2":round(hi-r*0.382,2),
"50":round(hi-r*0.5,2),
"61.8":round(hi-r*0.618,2),
"78.6":round(hi-r*0.786,2),
"100":round(lo,2)
}

def fib_extension(hi,lo,retr):
r=hi-lo
return {
"127.2":round(retr+r*1.272,2),
"161.8":round(retr+r*1.618,2),
"261.8":round(retr+r*2.618,2),
"423.6":round(retr+r*4.236,2)
}

def fib_projection(a,b,c):
r=abs(b-a)
return {
"61.8":round(c+r*0.618,2),
"100":round(c+r,2),
"161.8":round(c+r*1.618,2)
}

def golden_zone(hi,lo):
r=hi-lo
return round(hi-r*0.618,2),round(hi-r*0.786,2)

# === ELLIOTT WAVE BARCHA TURLARI ===

def detect_elliott(prices):
if len(prices)<30:return "Malumot yetarli emas"
p=prices[-30:]
pivots=[]
for i in range(2,len(p)-2):
if p[i]>p[i-1] and p[i]>p[i-2] and p[i]>p[i+1] and p[i]>p[i+2]:
pivots.append(("H",i,p[i]))
elif p[i]<p[i-1] and p[i]<p[i-2] and p[i]<p[i+1] and p[i]<p[i+2]:
pivots.append(("L",i,p[i]))
if len(pivots)<4:
trend="Yuqoriga" if p[-1]>p[0] else "Pastga"
return "Trend: "+trend+", Tolqin shakllanmoqda"
last=pivots[-4:]
types=[x[0] for x in last]
vals=[x[2] for x in last]
result=""
if types==["L","H","L","H"]:
if vals[3]>vals[1]:result="Impulse 3-tolqin (KUCHLI BUY)"
else:result="ABC Correction C-tolqin tugashi (BUY)"
elif types==["H","L","H","L"]:
if vals[3]<vals[1]:result="Impulse 3-tolqin (KUCHLI SELL)"
else:result="ABC Correction C-tolqin tugashi (SELL)"
elif types==["L","H","L","L"]:
result="Impulse 4-tolqin tugashi (BUY imkoniyati)"
elif types==["H","L","H","H"]:
result="Impulse 4-tolqin tugashi (SELL imkoniyati)"
else:
result="Tolqin kuzatilmoqda"
if len(pivots)>=6:
hh=[x[2] for x in pivots if x[0]=="H"][-3:]
ll=[x[2] for x in pivots if x[0]=="L"][-3:]
if len(hh)>=2 and len(ll)>=2:
if hh[-1]<hh[-2] and ll[-1]>ll[-2]:
result+=" | Triangle ABCDE (Breakout kutilmoqda)"
elif hh[-1]>hh[-2] and ll[-1]>ll[-2]:
result+=" | Diagonal (BUY trend)"
elif hh[-1]<hh[-2] and ll[-1]<ll[-2]:
result+=" | Diagonal (SELL trend)"
return result

def detect_patterns(prices,highs,lows):
patterns=[]
if len(prices)>=15:
seg=prices[-15:]
mx=max(seg);mi=seg.index(mx)
if 3<mi<11:
left=max(seg[:mi]);right=max(seg[mi+1:])
if mx>left*1.02 and mx>right*1.02 and abs(left-right)/mx<0.06:
patterns.append("Head & Shoulders (SELL)")
if len(lows)>=10:
l=lows[-10:]
mn=min(l);fi=l.index(mn)
rest=l[fi+2:]
if rest and min(rest)<mn*1.02:
patterns.append("Double Bottom (BUY)")
if len(highs)>=10:
h=highs[-10:]
mx=max(h);fi=h.index(mx)
rest=h[fi+2:]
if rest and max(rest)>mx*0.98:
patterns.append("Double Top (SELL)")
if len(prices)>=20:
recent=prices[-20:]
if recent[-1]>max(recent[:-1]):
patterns.append("Breakout (BUY)")
elif recent[-1]<min(recent[:-1]):
patterns.append("Breakdown (SELL)")
return patterns if patterns else ["Pattern aniqlanmadi"]

# === MA’LUMOT OLISH ===

def get_data(sym):
d=requests.get("https://api.coingecko.com/api/v3/coins/"+sym+"/market_chart",
params={"vs_currency":"usd","days":"3","interval":"hourly"},timeout=15).json()
prices=[x[1] for x in d["prices"]]
highs=[p*1.002 for p in prices]
lows=[p*0.998 for p in prices]
return prices,highs,lows

# === ASOSIY TAHLIL ===

def analyze_asset(sym,name,key,ch_thr=1.0):
try:
prices,highs,lows=get_data(sym)
pr=round(prices[-1],2)
r=rsi(prices)
m=macd_val(prices)
ch=round((prices[-1]-prices[-24])/prices[-24]*100,2)
hi24=max(prices[-24:]);lo24=min(prices[-24:])
fib_r=fib_retracement(hi24,lo24)
gz_hi,gz_lo=golden_zone(hi24,lo24)
if len(prices)>=48:
ph=max(prices[-48:-24]);pl=min(prices[-48:-24])
fib_e=fib_extension(ph,pl,lo24)
else:
fib_e={"161.8":round(pr*1.01618,2)}
if len(prices)>=72:
a=prices[-72];b=max(prices[-48:]);cc=min(prices[-24:])
fib_p=fib_projection(a,b,cc)
else:
fib_p={}
bb_lo,bb_mid,bb_hi=bollinger(prices)
sk=stoch_val(highs,lows,prices)
at=atr_val(highs,lows,prices)
elliott=detect_elliott(prices)
patterns=detect_patterns(prices,highs,lows)
sc=0
if r<30:sc+=3
elif r<40:sc+=2
elif r<45:sc+=1
elif r>70:sc-=3
elif r>60:sc-=2
elif r>55:sc-=1
if m>0:sc+=2
else:sc-=2
if ch>ch_thr:sc+=1
elif ch<-ch_thr:sc-=1
if pr<bb_lo:sc+=2
elif pr>bb_hi:sc-=2
elif pr<bb_mid:sc+=1
else:sc-=1
if gz_lo<=pr<=gz_hi:sc+=2
elif pr<fib_r[“61.8”]:sc+=1
elif pr>fib_r[“23.6”]:sc-=1
if sk<20:sc+=2
elif sk<30:sc+=1
elif sk>80:sc-=2
elif sk>70:sc-=1
if "BUY" in elliott:sc+=3
elif "SELL" in elliott:sc-=3
for pat in patterns:
if "BUY" in pat:sc+=2
elif "SELL" in pat:sc-=2
if sc>=8:sig="KUCHLI BUY"
elif sc>=4:sig="BUY"
elif sc<=-8:sig="KUCHLI SELL"
elif sc<=-4:sig="SELL"
else:sig="HOLD"
tp1=round(pr+at*2,2);tp2=round(pr+at*3.5,2);sl=round(pr-at*1.5,2)
if "SELL" in sig:
tp1=round(pr-at*2,2);tp2=round(pr-at*3.5,2);sl=round(pr+at*1.5,2)
last_data[key]={
"price":pr,"change":ch,"rsi":r,"macd":m,
"fib_r":fib_r,"fib_e":fib_e,"fib_p":fib_p,
"golden_zone":[gz_lo,gz_hi],"bb":[bb_lo,bb_mid,bb_hi],
"stoch":sk,"atr":at,"elliott":elliott,"patterns":patterns,
"score":sc,"signal":sig,"tp1":tp1,"tp2":tp2,"sl":sl,"name":name
}
emoji="KUCHLI BUY" if sc>=8 else "BUY" if sc>=4 else "KUCHLI SELL" if sc<=-8 else "SELL" if sc<=-4 else "HOLD"
sig_emoji=("KUCHLI BUY" if "KUCHLI BUY" in emoji else "BUY" if "BUY" in emoji else "KUCHLI SELL" if "KUCHLI SELL" in emoji else "SELL" if "SELL" in emoji else "HOLD")
return (name+" $"+str(pr)+" ("+str(ch)+"%)\n"
+"RSI:"+str(r)+" MACD:"+str(m)+" Stoch:"+str(sk)+"\n"
+"Golden Zone: $"+str(gz_lo)+"-$"+str(gz_hi)+"\n"
+"Fib 61.8%:$"+str(fib_r["61.8"])+"38.2%:$"+str(fib_r["38.2"])+"\n"
+"Ext 161.8%:$"+str(fib_e.get("161.8","?"))+"\n"
+"Elliott: "+elliott+"\n"
+"Pattern: "+", ".join(patterns)+"\n"
+"Signal: "+sig_emoji+" (ball:"+str(sc)+")\n"
+"TP1:$"+str(tp1)+" TP2:$"+str(tp2)+" SL:$"+str(sl))
except Exception as e:
return name+" xato: "+str(e)

def run_analysis():
try:
msg=(analyze_asset("bitcoin","BTC","btc")+"\n\n"
+analyze_asset("ethereum","ETH","eth")+"\n\n"
+analyze_asset("tether-gold","XAUUSD","gold",0.5))
send(msg)
except Exception as e:
print("Tahlil xato:"+str(e))

def get_news():
try:
today=datetime.datetime.now().strftime(”%Y-%m-%d”)
prompt=("Bugun "+today+" XAUUSD oltinga tasir qiladigan eng muhim 5 ta yangilikni yoz. Har biri: [emoji] [yangilik] -> [BULLISH/BEARISH/NEYTRAL]. Faqat shu formatda.")
r=requests.post("https://api.groq.com/openai/v1/chat/completions",
headers={"Authorization":“Bearer "+g,"Content-Type":"application/json"},
json={"model":"llama3-70b-8192","messages":[{"role":"user","content":prompt}],"max_tokens":600},timeout=30)
return r.json()["choices"][0]["message"]["content"]
except Exception as e:
return "Yangiliklar yuklanmadi: "+str(e)

def send(msg):
try:
requests.post("https://api.telegram.org/bot"+t+"/sendMessage",
json={"chat_id":c,"text":msg},timeout=10)
except:pass

HTML=open("template.html").read() if os.path.exists("template.html") else "<h1>Bot ishlayapti</h1>"

@app.route("/")
def index():
return HTML

@app.route("/api/signals")
def api_signals():
return jsonify(last_data)

@app.route("/api/news")
def api_news():
try:
return jsonify({"news":get_news()})
except:
return jsonify({"news":"Xato yuz berdi"})

def check_commands():
global running,offset
while True:
try:
r=requests.get("https://api.telegram.org/bot"+t+"/getUpdates",
params={"offset":offset,"timeout":10},timeout=15).json()
for u in r.get("result",[]):
offset=u["update_id"]+1
txt=u.get("message",{}).get("text","")
if txt=="/start":
running=True
send("Bot ishga tushdi!")
run_analysis()
elif txt=="/stop":
running=False
send("Bot toxtatildi. /start bilan qayta boshlang.")
elif txt==”/signal”:
send("Tahlil qilinmoqda…")
run_analysis()
elif txt=="/news":
send("Yangiliklar qidirilmoqda…")
send("XAUUSD YANGILIKLAR\n\n"+get_news()+"\n\nBu AI tahlili!")
elif txt=="/help":
send("/start /stop /signal /news /help")
except Exception as e:
print("Command xato:"+str(e))
time.sleep(3)

def signal_loop():
while True:
if running:
run_analysis()
time.sleep(900)

threading.Thread(target=check_commands,daemon=True).start()
threading.Thread(target=signal_loop,daemon=True).start()
send("Bot ishga tushdi! /start /stop /signal /news /help")
app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))
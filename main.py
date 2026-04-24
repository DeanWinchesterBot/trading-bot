import os,requests,time
t=os.environ.get("TELEGRAM_TOKEN")
c=os.environ.get("CHAT_ID")
def rsi(prices,n=14):
 gains,losses=[],[]
 for i in range(1,len(prices)):
  d=prices[i]-prices[i-1]
  gains.append(max(d,0))
  losses.append(max(-d,0))
 ag=sum(gains[-n:])/n
 al=sum(losses[-n:])/n
 if al==0:return 100
 return round(100-100/(1+ag/al),1)
def macd(prices):
 def ema(p,n):
  k=2/(n+1);e=p[0]
  for x in p[1:]:e=x*k+e*(1-k)
  return e
 return round(ema(prices,12)-ema(prices,26),2)
def crypto(sym,name):
 d=requests.get("https://api.coingecko.com/api/v3/coins/"+sym+"/market_chart",params={"vs_currency":"usd","days":"2","interval":"hourly"},timeout=15).json()
 prices=[x[1] for x in d["prices"]]
 p=round(prices[-1],2)
 r=rsi(prices)
 m=macd(prices)
 ch=round((prices[-1]-prices[-24])/prices[-24]*100,2)
 hi=max(prices[-24:]);lo=min(prices[-24:])
 f1=round(lo+(hi-lo)*0.382,2);f2=round(lo+(hi-lo)*0.618,2)
 score=0
 if r<35:score+=2
 elif r<45:score+=1
 elif r>65:score-=2
 elif r>55:score-=1
 if m>0:score+=1
 else:score-=1
 if ch>1:score+=1
 elif ch<-1:score-=1
 if p<f1:score+=1
 elif p>f2:score-=1
 if score>=3:sig="KUCHLI BUY 🟢🟢"
 elif score>=1:sig="BUY 🟢"
 elif score<=-3:sig="KUCHLI SELL 🔴🔴"
 elif score<=-1:sig="SELL 🔴"
 else:sig="HOLD 🟡"
 return name+" $"+str(p)+" ("+str(ch)+"%)\nRSI: "+str(r)+" | MACD: "+str(m)+"\nFib: $"+str(f1)+" | $"+str(f2)+"\nSignal: "+sig+" (ball: "+str(score)+")"
def gold():
 d=requests.get("https://api.metals.live/v1/spot/gold",timeout=10).json()
 p=round(float(d[0]["price"]),2)
 d2=requests.get("https://api.coingecko.com/api/v3/simple/price",params={"ids":"tether-gold","vs_currencies":"usd","include_24hr_change":"true"},timeout=10).json()
 ch=round(d2["tether-gold"]["usd_24h_change"],2)
 if ch>0.5:sig="BUY 🟢"
 elif ch<-0.5:sig="SELL 🔴"
 else:sig="HOLD 🟡"
 return "XAUUSD $"+str(p)+" ("+str(ch)+"%)\nSignal: "+sig
while True:
 try:
  msg=crypto("bitcoin","BTC")+"\n\n"+crypto("ethereum","ETH")+"\n\n"+gold()
  requests.post("https://api.telegram.org/bot"+t+"/sendMessage",json={"chat_id":c,"text":msg})
 except Exception as e:
  print(str(e))
 time.sleep(900)

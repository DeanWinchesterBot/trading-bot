import os,requests,time,json
t=os.environ.get("TELEGRAM_TOKEN")
c=os.environ.get("CHAT_ID")
def get_data(symbol):
 r=requests.get("https://api.coingecko.com/api/v3/coins/"+symbol+"/market_chart",params={"vs_currency":"usd","days":"2","interval":"hourly"},timeout=15)
 return r.json()["prices"]
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
def signal(sym,name):
 data=get_data(sym)
 prices=[x[1] for x in data]
 p=round(prices[-1],2)
 r=rsi(prices)
 m=macd(prices)
 ch=round((prices[-1]-prices[-24])/prices[-24]*100,2)
 hi=round(max(prices[-24:]),2)
 lo=round(min(prices[-24:]),2)
 fib1=round(lo+(hi-lo)*0.382,2)
 fib2=round(lo+(hi-lo)*0.618,2)
 score=0
 if r<35:score+=2
 elif r<45:score+=1
 elif r>65:score-=2
 elif r>55:score-=1
 if m>0:score+=1
 else:score-=1
 if ch>1:score+=1
 elif ch<-1:score-=1
 if p<fib1:score+=1
 elif p>fib2:score-=1
 if score>=3:sig="KUCHLI BUY 🟢🟢"
 elif score>=1:sig="BUY 🟢"
 elif score<=-3:sig="KUCHLI SELL 🔴🔴"
 elif score<=-1:sig="SELL 🔴"
 else:sig="HOLD 🟡"
 return name+" $"+str(p)+" ("+str(ch)+"%)\nRSI: "+str(r)+" | MACD: "+str(m)+"\nFib support: $"+str(fib1)+" | resistance: $"+str(fib2)+"\nSignal: "+sig+" (ball: "+str(score)+")"
while True:
 try:
  msg=signal("bitcoin","BTC")+"\n\n"+signal("ethereum","ETH")
  requests.post("https://api.telegram.org/bot"+t+"/sendMessage",json={"chat_id":c,"text":msg})
 except Exception as e:
  print(str(e))
 time.sleep(900)

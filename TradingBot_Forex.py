#!/usr/bin/env python
# coding: utf-8

# ### 1 - Import test data

# In[2]:


import yfinance as yf
import pandas as pd

dataF = yf.download("EURUSD=X", start="2023-07-01", end="2023-08-16", interval='15m')
dataF.iloc[:,:]
#dataF.Open.iloc


# ### 2 - Define your signal function

# In[3]:


def signal_generator(df):
    open = df.Open.iloc[-1]
    close = df.Close.iloc[-1]
    previous_open = df.Open.iloc[-2]
    previous_close = df.Close.iloc[-2]
    
    # Bearish Pattern
    if (open>close and 
    previous_open<previous_close and 
    close<previous_open and
    open>=previous_close):
        return 1

    # Bullish Pattern
    elif (open<close and 
        previous_open>previous_close and 
        close>previous_open and
        open<=previous_close):
        return 2
    
    # No clear pattern
    else:
        return 0

signal = []
signal.append(0)
for i in range(1,len(dataF)):
    df = dataF[i-1:i+1]
    signal.append(signal_generator(df))
#signal_generator(data)
dataF["signal"] = signal


# In[4]:


dataF.signal.value_counts()
#dataF.iloc[:, :]


# ### 3 - Connect to the market and execute trades

# In[8]:


from apscheduler.schedulers.blocking import BlockingScheduler
from oandapyV20 import API
import oandapyV20.endpoints.orders as orders
from oandapyV20.contrib.requests import MarketOrderRequest
from oanda_candles import Pair, Gran, CandleClient
from oandapyV20.contrib.requests import TakeProfitDetails, StopLossDetails


# In[12]:


def get_candles(n):
    access_token= '48cff0b32bead49de82ab94055b0a688-d0b5dd675d17e5800ae16c0866c9b43c'
    client = CandleClient(access_token, real=False)
    collector = client.get_collector(Pair.EUR_USD, Gran.M15)
    candles = collector.grab(n)
    return candles

candles = get_candles(3)
for candle in candles:
    print(float(str(candle.bid.o))>1)


# In[20]:


def trading_job():
    access_token= '48cff0b32bead49de82ab94055b0a688-d0b5dd675d17e5800ae16c0866c9b43c'
    accountID = '101-004-26615381-001'
    candles = get_candles(3)
    dfstream = pd.DataFrame(columns=['Open','Close','High','Low'])
    
    i=0
    for candle in candles:
        dfstream.loc[i, ['Open']] = float(str(candle.bid.o))
        dfstream.loc[i, ['Close']] = float(str(candle.bid.c))
        dfstream.loc[i, ['High']] = float(str(candle.bid.h))
        dfstream.loc[i, ['Low']] = float(str(candle.bid.l))
        i=i+1

    dfstream['Open'] = dfstream['Open'].astype(float)
    dfstream['Close'] = dfstream['Close'].astype(float)
    dfstream['High'] = dfstream['High'].astype(float)
    dfstream['Low'] = dfstream['Low'].astype(float)

    signal = signal_generator(dfstream.iloc[:-1,:])#
    
    # EXECUTING ORDERS
    #accountID = "XXXXXXX" #your account ID here
    client = API(access_token)
         
    SLTPRatio = 2.
    previous_candleR = abs(dfstream['High'].iloc[-2]-dfstream['Low'].iloc[-2])
    
    SLBuy = float(str(candle.bid.o))-previous_candleR
    SLSell = float(str(candle.bid.o))+previous_candleR

    TPBuy = float(str(candle.bid.o))+previous_candleR*SLTPRatio
    TPSell = float(str(candle.bid.o))-previous_candleR*SLTPRatio
    
    print(dfstream.iloc[:-1,:])
    print(TPBuy, "  ", SLBuy, "  ", TPSell, "  ", SLSell)
    signal = 2
    #Sell
    if signal == 1:
        mo = MarketOrderRequest(instrument="EUR_USD", units=-10000, takeProfitOnFill=TakeProfitDetails(price=TPSell).data, stopLossOnFill=StopLossDetails(price=SLSell).data)
        r = orders.OrderCreate(accountID, data=mo.data)
        rv = client.request(r)
        print(rv)
    #Buy
    elif signal == 2:
        mo = MarketOrderRequest(instrument="EUR_USD", units=10000, takeProfitOnFill=TakeProfitDetails(price=TPBuy).data, stopLossOnFill=StopLossDetails(price=SLBuy).data)
        r = orders.OrderCreate(accountID, data=mo.data)
        rv = client.request(r)
        print(rv)


# ### 4 - Executing orders automatically with a scheduler

# In[21]:


trading_job()

#scheduler = BlockingScheduler()
#scheduler.add_job(trading_job, 'cron', day_of_week='mon-fri', hour='00-23', minute='1,16,31,46', start_date='2022-01-12 12:00:00', timezone='America/Chicago')
#scheduler.start()


# In[ ]:





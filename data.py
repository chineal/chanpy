import os
import akshare as ak
import pandas as pd
from datetime import datetime
from glob import glob

#from dateutil.relativedelta import relativedelta

# 获取当前日期时间
#now = datetime.datetime.now()

# 加上三个月
#last_month = now - relativedelta(months=1)
#last_month_str = last_month.strftime('%Y-%m-%d')#%Y-%m-%d %H:%M:%S
#print(last_month_str)

#futures_main_sina_df = ak.futures_main_sina(symbol='IF0', start_date=last_month_str)
#print(futures_main_sina_df)

datas = {}
bigest = 0

def history(m):
    global datas
    global bigest

    try:
        df = pd.read_csv("datas/if9999.csv", encoding="utf-8")
        #print(df.index)
        #print(df.iloc[[0]])
        #print(df.iloc[:,0])

        cols = []
        for col in df:
            cols.append(col)
        cols[0] = 'datime'
        print(cols)

        list = df.values.tolist()
        recode = 0
        for item in list:
            dt = datetime.strptime(item[0], "%Y-%m-%d %H:%M:%S")
            date = int(dt.strftime('%y%m%d'))
            if recode != date:
                if recode != 0:
                    df = pd.DataFrame(datas)
                    df.to_csv('./datas/m%d/%d.csv' % (m, recode), index=False)
                recode = date
                for col in cols:
                    datas[col] = []
            i = 0
            for col in cols:
                datas[col].append(item[i])
                i += 1
        df = pd.DataFrame(datas)
        df.to_csv('./datas/m%d/%d.csv' % (m, recode), index=False)
    except Exception as e:
        pass

    csvs = glob('./datas/m%d/*.csv' % m)
    for csv in csvs:
        last = csv.rfind('\\')
        date = int(csv[last + 1 : -4])
        if date > bigest:
            bigest = date
    print('bigest:%d' % bigest)

def current(m):
    global datas
    global bigest

    futures_zh_minute_sina_df = ak.futures_zh_minute_sina(symbol='IF0', period=str(m))
    for col in futures_zh_minute_sina_df:
        print('futures_zh_minute_sina_col:%s' % col)

    recode = 0
    list = futures_zh_minute_sina_df.values.tolist()
    for item in list:
        dt = datetime.strptime(item[0], "%Y-%m-%d %H:%M:%S")
        date = int(dt.strftime('%y%m%d'))
        if date <= bigest:
            continue
        if recode != date:
            if recode != 0:
                df = pd.DataFrame(datas)
                df.to_csv('./datas/m%d/%d.csv' % (m, recode), index=False)
            recode = date
            datas['datime'] = []
            datas['open'] = []
            datas['close'] = []
            datas['high'] = []
            datas['low'] = []
            datas['volume'] = []
            datas['money'] = []
        datas['datime'].append(item[0])
        datas['open'].append(item[1])
        datas['close'].append(item[4])
        datas['high'].append(item[2])
        datas['low'].append(item[3])
        datas['volume'].append(item[5])
        datas['money'].append(item[6])
        
    if recode != 0:
        df = pd.DataFrame(datas)
        df.to_csv('./datas/m%d/%d.csv' % (m, recode), index=False)

history(1)
#current(1)
#current(5)
#current(30)
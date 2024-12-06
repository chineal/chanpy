import ctypes
import os

import akshare as ak
from datetime import datetime

import schedule
import time

from dateutil.relativedelta import relativedelta
from glob import glob
import pandas as pd

current_path    = os.getcwd()
os.add_dll_directory(current_path)
rust_chan_dll   = ctypes.CDLL('rust_chan.dll')

def f2p(number):
    return ctypes.pointer(ctypes.c_float(number))

historys = []
bigest = 0
nexter = 0
def recode(day):
    global historys
    global bigest
    global nexter
    historys = []
    bigest = 0
    nexter = 0
    last_month = day - relativedelta(months=1)
    start = int(last_month.strftime('%y%m%d'))
    end = int(day.strftime('%y%m%d'))
    files = []
    csvs = glob('.\datas\*.csv')
    for csv in csvs:
        date = int(csv[8:-4])
        if date >= end:
            nexter = date
            break
        if date >= start:
            files.append(date)
    files.sort()
    bigest = files[-1]
    for file in files:
        df = pd.read_csv('.\datas\%d.csv' % file, encoding='utf-8')
        historys.extend(df.values.tolist())

closed = 0
opened = 0
openly = 0
opener = 0
rust_chan_dll.RegisterCpyInit()
def daily(length):
    global historys
    global bigest
    global nexter
    global closed
    global opened
    global openly
    global opener

    if length > 0 and nexter > 0:
        df = pd.read_csv('.\datas\%d.csv' % nexter, encoding='utf-8')
        currents = df.values.tolist()[:length]
    else:
        futures_zh_minute_sina_df = ak.futures_zh_minute_sina(symbol='IF0', period='1')
        currents = futures_zh_minute_sina_df.values.tolist()
    start = 0
    for current in currents:
        dt      = datetime.strptime(current[0], "%Y-%m-%d %H:%M:%S")
        date    = int(dt.strftime('%y%m%d'))
        if date > bigest:
            break
        start   += 1
        
    count = len(historys) + (len(currents) - start)
    buf = ctypes.c_float * count
    out = buf()

    dates   = buf()
    times   = buf()
    highs   = buf()
    lows    = buf()
    closes  = buf()

    mhs     = buf()
    mls     = buf()
    chs     = buf()
    cls     = buf()
    fracs   = buf()

    i = 0
    for history in historys:
        dt          = datetime.strptime(history[0], "%Y-%m-%d %H:%M:%S")
        dates[i]    = int(dt.strftime('%y%m%d'))
        times[i]    = int(dt.strftime('%H%M%S'))
        highs[i]    = history[3]
        lows[i]     = history[4]
        closes[i]   = history[2]
        i += 1
    for j in range(start, len(currents)):
        dt          = datetime.strptime(currents[j][0], "%Y-%m-%d %H:%M:%S")
        dates[i]    = int(dt.strftime('%y%m%d'))
        times[i]    = int(dt.strftime('%H%M%S'))
        highs[i]    = currents[j][2]
        lows[i]     = currents[j][3]
        closes[i]   = currents[j][4]
        i += 1

    #print('data:%d-%d time:%d' % (dates[0], dates[count - 1], times[count - 1]))
    period  = f2p(0)

    result = rust_chan_dll.RegisterCpyFunc(2, count, mhs, highs, lows, f2p(1))
    result = rust_chan_dll.RegisterCpyFunc(2, count, mls, highs, lows, f2p(-1))
    for i in range(count):
        chs[i] = mhs[i] if mhs[i]>0 else highs[i]
        cls[i] = mls[i] if mls[i]>0 else lows[i]

    result = rust_chan_dll.RegisterCpyFunc(3, count, fracs, highs, lows, f2p(13))

    result = rust_chan_dll.RegisterCpyFunc(4, count, out, f2p(0),   period, f2p(9))
    result = rust_chan_dll.RegisterCpyFunc(4, count, out, f2p(1),   period, f2p(0))
    result = rust_chan_dll.RegisterCpyFunc(4, count, out, f2p(11),  period, dates)
    result = rust_chan_dll.RegisterCpyFunc(4, count, out, f2p(12),  period, times)
    result = rust_chan_dll.RegisterCpyFunc(4, count, out, f2p(13),  period, fracs)
    result = rust_chan_dll.RegisterCpyFunc(4, count, out, f2p(14),  period, chs)
    result = rust_chan_dll.RegisterCpyFunc(4, count, out, f2p(15),  period, cls)
    result = rust_chan_dll.RegisterCpyFunc(4, count, out, f2p(16),  period, closes)
    result = rust_chan_dll.RegisterCpyFunc(4, count, out, f2p(17),  period, highs)
    result = rust_chan_dll.RegisterCpyFunc(4, count, out, f2p(18),  period, lows)
    result = rust_chan_dll.RegisterCpyFunc(4, count, out, f2p(99),  period, f2p(0))
    #print('result:%d out:%d' % (result, out[0]))

    for i in range(count):
        out[i] = 0
    result = rust_chan_dll.RegisterCpyFunc(5, count, out, f2p(0), f2p(0), period)
    duan = 0
    for i in range(count):
        if out[i] == 1:
            duan += 1

    ods     = buf()
    open    = 0
    result = rust_chan_dll.RegisterCpyFunc(7, count, ods, f2p(0), f2p(0), period)
    for i in range(count):
        if ods[i] == 2 or ods[i] == -2:
            open = i

    cds     = buf()
    close   = 0
    result = rust_chan_dll.RegisterCpyFunc(7, count, cds, f2p(0), f2p(1), period)
    for i in range(count):
        if cds[i] == 4 or cds[i] == -4:
            close = i
    
    oss = buf()
    result = rust_chan_dll.RegisterCpyFunc(6, count, oss, f2p(12), f2p(6), period)

    if open > 0:
        t = dates[open] * 1000000 + times[open]
        if opened != t:
            if t > opened:
                openly = ods[open]
                opener = highs[-1] if openly > 0 else lows[-1]
                print('open date:%d(%d)-%d(%d) index:%d flag:%d %s value:%.2f' %(
                    dates[open],
                    dates[-1],
                    times[open],
                    times[-1],
                    open,
                    oss[open],
                    'enter long' if openly > 0 else 'enter short',
                    opener))
            if opened > t and openly != 0:
                temp = highs[-1] if openly > 0 else lows[-1]
                print('last date:%d-%d lost point value:%.2f' %(dates[-1], times[-1], temp))
                openly = 0
            opened = t

    if close > 0:
        t = dates[close] * 1000000 + times[close]
        if closed != t:
            if t > closed:
                temp = highs[-1] if openly > 0 else lows[-1]
                print('close date:%d(%d)-%d(%d) indes:%d %s value:%.2f' %(
                    dates[close],
                    dates[-1],
                    times[close],
                    times[-1],
                    close,
                    'exit long' if cds[close] < 0 else 'exit short',
                    temp))
                if (openly > 0 and cds[close] < 0) or (openly < 0 and cds[close] > 0):
                    openly = 0
            closed = t


def run():
    daily(0)
def sched_chan():
    schedule.every().minute.at(":01").do(run).tag("s_chan")
    print("chan runing")
def clear_chan():
    schedule.clear("s_chan")
    print("chan stoped")
schedule.every().day.at('09:29:55').do(sched_chan)
schedule.every().day.at('12:59:55').do(sched_chan)
schedule.every().day.at('11:30:05').do(clear_chan)
schedule.every().day.at('15:00:05').do(clear_chan)

def schedule_chan():
    recode(datetime.now())
    sched_chan()
    while True:
        schedule.run_pending()
        time.sleep(1)

def backtest_chan():
    st = time.time()
    start = datetime.strptime('2023-09-23 09:30:00', '%Y-%m-%d %H:%M:%S')
    for j in range(30):
        start = start + relativedelta(days=1)
        flag = int(start.strftime('%y%m%d'))
        if os.path.exists('.\datas\%d.csv' % flag):
            recode(start)
            for i in range(((11-9)+(15-13))*60):
                daily(i+1)
    print("耗时: {:.2f}秒".format(time.time() - st))

if __name__ == "__main__":
    #schedule_chan()
    backtest_chan()
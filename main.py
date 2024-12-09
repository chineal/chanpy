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

historys = []   #历史数据加载
bigest = 0      #最大历史数据
nexter = 0      #运行数据开始
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
    print('data start:%d data size:%d file count:%d' %(start, len(historys), len(files)))

trade_count     = 0 #交易数量
enter_count     = 0 #开仓数量
enter_longs     = 0 #买开数量
enter_shorts    = 0 #卖开数量
exit_count      = 0 #平仓数量
exit_longs      = 0 #卖平数量
exit_shorts     = 0 #买平数量
profit_count    = 0 #盈亏统计
def init():
    global trade_count
    global enter_count
    global enter_longs
    global enter_shorts
    global exit_count
    global exit_longs
    global exit_shorts
    global profit_count
    trade_count     = 0
    enter_count     = 0
    enter_longs     = 0
    enter_shorts    = 0
    exit_count      = 0
    exit_longs      = 0
    exit_shorts     = 0
    profit_count    = 0

closed = 0  #平仓点数量记录
opened = 0  #开仓点数量记录
openly = 0  #开仓点方向记录
opener = 0  #开仓点数值记录
openat = 0  #开仓时间戳记录
openid = 0  #开仓点标识记录
rust_chan_dll.RegisterCpyInit()
def daily(length):
    global historys
    global bigest
    global nexter
    global closed
    global opened
    global openly
    global opener
    global openat
    global openid

    global trade_count
    global enter_count
    global enter_longs
    global enter_shorts
    global exit_count
    global exit_longs
    global exit_shorts
    global profit_count

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
                lates = (len(dates) - open) - 1
                if openat == 0:
                    openid = t
                    openly = ods[open]
                    opener = closes[-1]
                    openat = dates[-1] * 1000000 + times[-1]

                print('open  at date:%d(%d)-%d(%d) lates:%d index:%d %s value:%.2f flag:%d' %(
                    dates[open],
                    dates[-1],
                    times[open],
                    times[-1],
                    lates,
                    closes[-1],
                    'enter long' if ods[open] > 0 else 'enter short',
                    opener,
                    oss[open]))
            if opened > t and openly != 0:
                index = -1
                for i in range(count):
                    if dates[i] * 1000000 + times[i] == openid:
                        index = i
                if index >=0 and ods[index] == 0:
                    lates = (len(dates) - index) - 1
                    closat = dates[-1] * 1000000 + times[-1]
                    closer = closes[-1]

                    if closat - openat > 0 and openat > 0:
                        trade_count += 1
                        enter_count += 1
                        if openly > 1:
                            enter_longs += 1
                        else:
                            enter_shorts += 1
                            
                        trade_count += 1
                        exit_count  += 1
                        if openly > 0:
                            exit_longs += 1
                            profit_count += (closer - opener)
                            profit = '%.2f' % (closer - opener)
                        else:
                            exit_shorts += 1
                            profit_count += (opener - closer)
                            profit = '%.2f' % (opener - closer)
                    else: 
                        profit = 'null'

                    openid = 0
                    openat = 0
                    openly = 0
                    print('lost  at date:%d-%d lates:%d point value:%.2f profit:%s' %(dates[-1], times[-1], lates, closer, profit))
            opened = t

    if close > 0:
        t = dates[close] * 1000000 + times[close]
        if closed != t:
            if t > closed:
                closat = dates[-1] * 1000000 + times[-1]
                closer = closes[-1]
                lates = (len(dates) - close) - 1

                if closat - openat > 0 and openat > 0:
                    trade_count += 1
                    enter_count += 1
                    if openly > 1:
                        enter_longs += 1
                    else:
                        enter_shorts += 1
                            
                    trade_count += 1
                    exit_count  += 1
                    if openly > 0:
                        exit_longs += 1
                        profit_count += (closer - opener)
                        profit = '%.2f' % (closer - opener)
                    else:
                        exit_shorts += 1
                        profit_count += (opener - close)
                        profit = '%.2f' % (opener - closer)
                else: 
                    profit = 'null'

                openid = 0
                openat = 0
                openly = 0
                
                print('close at date:%d(%d)-%d(%d) lates:%d index:%d %s value:%.2f profit:%s' %(
                    dates[close],
                    dates[-1],
                    times[close],
                    times[-1],
                    lates,
                    close,
                    'exit  long' if cds[close] < 0 else 'exit  short',
                    closer,
                    profit))
            closed = t

def run():
    daily(0)
def sched_chan():
    init()
    recode(datetime.now())
    schedule.every().minute.at(':01').do(run).tag('s_chan')
    print('chan runing')
def clear_chan():
    global trade_count
    global enter_count
    global enter_longs
    global enter_shorts
    global exit_count
    global exit_longs
    global exit_shorts
    global profit_count
    print('trade:%d enter:%d %d %d exit:%d %d %d profit:%.2f' % (
        trade_count, enter_count, enter_longs, enter_shorts,
        exit_count, exit_longs, exit_shorts, profit_count))
    schedule.clear('s_chan')
    print('chan stoped')
schedule.every().day.at('09:29:55').do(sched_chan)
schedule.every().day.at('12:59:55').do(sched_chan)
schedule.every().day.at('11:30:05').do(clear_chan)
schedule.every().day.at('15:00:05').do(clear_chan)

def schedule_chan():
    sched_chan()
    while True:
        schedule.run_pending()
        time.sleep(1)

def backtest_chan():
    global trade_count
    global enter_count
    global enter_longs
    global enter_shorts
    global exit_count
    global exit_longs
    global exit_shorts
    global profit_count
    
    init()
    st = time.time()
    start = datetime.strptime('2024-11-09 09:30:00', '%Y-%m-%d %H:%M:%S')
    for j in range(30):
        flag = int(start.strftime('%y%m%d'))
        if os.path.exists('.\datas\%d.csv' % flag):
            recode(start)
            for i in range(((11-9)+(15-13))*60):
                daily(i+1)
            print('trade:%d enter:%d %d %d exit:%d %d %d profit:%.2f' % (
                trade_count, enter_count, enter_longs, enter_shorts,
                exit_count, exit_longs, exit_shorts, profit_count))
        start = start + relativedelta(days=1)
    print('耗时: {:.2f}秒'.format(time.time() - st))

if __name__ == "__main__":
    #schedule_chan()
    backtest_chan()
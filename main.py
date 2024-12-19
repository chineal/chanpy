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

class chan:
    historys        = []#历史数据加载
    bigest          = 0 #最大历史数据
    nexter          = 0 #运行数据开始
    closed          = 0 #平仓点数量记录
    opened          = 0 #开仓点数量记录
    openly          = 0 #开仓点方向记录
    opener          = 0 #开仓点数值记录
    openat          = 0 #开仓时间戳记录
    openid          = 0 #开仓点标识记录
    trade_count     = 0 #交易数量
    enter_count     = 0 #开仓数量
    enter_longs     = 0 #买开数量
    enter_shorts    = 0 #卖开数量
    exit_count      = 0 #平仓数量
    exit_longs      = 0 #卖平数量
    exit_shorts     = 0 #买平数量
    profit_count    = 0 #盈亏统计
    lost_count      = 0 #开仓点消失统计
    
    def loads(self, start, end, path):
        self.historys   = []
        self.bigest     = 0
        self.nexter     = 0
        files           = []
        csvs            = glob('%s/*.csv' % path)
        for csv in csvs:
            last = csv.rfind('\\')
            date = int(csv[last + 1 : -4])
            if date >= end:
                self.nexter = date
                break
            if date >= start:
                files.append(date)
        files.sort()
        self.bigest = files[-1]
        for file in files:
            df = pd.read_csv('%s/%d.csv' % (path, file), encoding='utf-8')
            self.historys.extend(df.values.tolist())
        print('data start:%d data size:%d file count:%d' %(start, len(self.historys), len(files)))

    def recode(self, day, prevs, path):
        last_month = day - relativedelta(months=prevs)
        start = int(last_month.strftime('%y%m%d'))
        end = int(day.strftime('%y%m%d'))
        self.loads(start, end, path)

    def init(self):
        self.trade_count    = 0
        self.enter_count    = 0
        self.enter_longs    = 0
        self.enter_shorts   = 0
        self.exit_count     = 0
        self.exit_longs     = 0
        self.exit_shorts    = 0
        self.profit_count   = 0
        self.lost_count     = 0

    def currently(self, length, path, flag):
        if length > 0 and self.nexter > 0:
            high  = 3
            low   = 4
            close = 2
            df = pd.read_csv('%s/%d.csv' % (path, self.nexter), encoding='utf-8')
            currents = df.values.tolist()[:length]
        else:
            high  = 2
            low   = 3
            close = 4
            futures_zh_minute_sina_df = ak.futures_zh_minute_sina(symbol='IF0', period=str(flag))
            currents = futures_zh_minute_sina_df.values.tolist()
        start = 0
        for current in currents:
            dt      = datetime.strptime(current[0], "%Y-%m-%d %H:%M:%S")
            date    = int(dt.strftime('%y%m%d'))
            if date > self.bigest:
                break
            start   += 1
        return currents, high, low, close, start

    def currenter(self, length, path, flag):
        currents, high, low, close, start = self.currently(length, path, flag)
        return currents, close, start
    
    def input(self, length, path, flag, key):
        currents, high, low, close, start = self.currently(length, path, flag)
        return self._call(key, currents, high, low, close, start)

    def output(self, count, length, path, flag, key):
        period  = f2p(key)
        buf = ctypes.c_float * count

        out = buf()
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
        result = rust_chan_dll.RegisterCpyFunc(6, count, oss, f2p(13), f2p(2), period)

        dates = []
        times = []
        closes = []
        for history in self.historys:
            dt = datetime.strptime(history[0], "%Y-%m-%d %H:%M:%S")
            dates.append(int(dt.strftime('%y%m%d')))
            times.append(int(dt.strftime('%H%M%S')))
            closes.append(history[2])
        
        currents, index_close, start = self.currenter(length, path, flag)
        for j in range(start, len(currents)):
            dt          = datetime.strptime(currents[j][0], "%Y-%m-%d %H:%M:%S")
            dates.append(int(dt.strftime('%y%m%d')))
            times.append(int(dt.strftime('%H%M%S')))
            closes.append(currents[j][index_close])
        
        if open > 0:
            t = dates[open] * 1000000 + times[open]
            if self.opened != t:
                if t > self.opened:
                    lates = (len(dates) - open) - 1
                    if self.openat == 0:
                        self.openid = t
                        self.openly = ods[open]
                        self.opener = closes[-1]
                        self.openat = dates[-1] * 1000000 + times[-1]

                    print('open  at date:%d(%d)-%d(%d) lates:%d index:%d %s value:%.2f flag:%.2f' %(
                        dates[open],
                        dates[-1],
                        times[open],
                        times[-1],
                        lates,
                        closes[-1],
                        'enter long' if ods[open] > 0 else 'enter short',
                        self.opener,
                        oss[open]))
                if self.opened > t and self.openly != 0:
                    index = -1
                    for i in range(count):
                        if dates[i] * 1000000 + times[i] ==self. openid:
                            index = i
                    if index >=0 and ods[index] == 0:
                        lates = (len(dates) - index) - 1
                        closat = dates[-1] * 1000000 + times[-1]
                        closer = closes[-1]

                        if closat - self.openat > 0 and self.openat > 0:
                            self.trade_count += 1
                            self.enter_count += 1
                            self.lost_count  += 1
                            if self.openly > 1:
                                self.enter_longs += 1
                            else:
                                self.enter_shorts += 1
                                
                            self.trade_count += 1
                            self.exit_count  += 1
                            if self.openly > 0:
                                self.exit_longs += 1
                                self.profit_count += (closer - self.opener)
                                profit = '%.2f' % (closer - self.opener)
                            else:
                                self.exit_shorts += 1
                                self.profit_count += (self.opener - closer)
                                profit = '%.2f' % (self.opener - closer)
                        else: 
                            profit = 'null'

                        self.openid = 0
                        self.openat = 0
                        self.openly = 0
                        print('lost  at date:%d-%d lates:%d point value:%.2f profit:%s' %(dates[-1], times[-1], lates, closer, profit))
                self.opened = t

        if close > 0:
            t = dates[close] * 1000000 + times[close]
            if self.closed != t:
                if t > self.closed:
                    closat = dates[-1] * 1000000 + times[-1]
                    closer = closes[-1]
                    lates = (len(dates) - close) - 1

                    if closat - self.openat > 0 and self.openat > 0:
                        self.trade_count += 1
                        self.enter_count += 1
                        if self.openly > 1:
                            self.enter_longs += 1
                        else:
                            self.enter_shorts += 1
                                
                        self.trade_count += 1
                        self.exit_count  += 1
                        if self.openly > 0:
                            self.exit_longs += 1
                            self.profit_count += (closer - self.opener)
                            profit = '%.2f' % (closer - self.opener)
                        else:
                            self.exit_shorts += 1
                            self.profit_count += (self.opener - closer)
                            profit = '%.2f' % (self.opener - closer)
                    else: 
                        profit = 'null'

                    self.openid = 0
                    self.openat = 0
                    self.openly = 0
                    
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
                self.closed = t

    def _call(self, key, currents, index_high, index_low, index_close, start):
        count = len(self.historys) + (len(currents) - start)
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
        for history in self.historys:
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
            highs[i]    = currents[j][index_high]
            lows[i]     = currents[j][index_low]
            closes[i]   = currents[j][index_close]
            i += 1

        #print('data:%d-%d time:%d' % (dates[0], dates[count - 1], times[count - 1]))
        period  = f2p(key)

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
        return count

chan_max = chan()
chan_mid = chan()
chan_min = chan()

def run():
    count = chan_min.input(0, './datas/m1', 1, 0)
    chan_min.output(count, 0, './datas/m1', 1, 0)
def sched_chan():
    chan_min.init()
    chan_min.recode(datetime.now(), 1, './datas/m1')
    schedule.every().minute.at(':01').do(run).tag('s_chan')
    print('chan runing')
def clear_chan():
    print('trade:%d enter:%d %d %d exit:%d %d %d lost:%d profit:%.2f' % (
        chan_min.trade_count, chan_min.enter_count, chan_min.enter_longs, chan_min.enter_shorts,
        chan_min.exit_count, chan_min.exit_longs, chan_min.exit_shorts, chan_min.lost_count, chan_min.profit_count))
    schedule.clear('s_chan')
    print('chan stoped')
schedule.every().day.at('09:29:55').do(sched_chan)
schedule.every().day.at('12:59:55').do(sched_chan)
schedule.every().day.at('11:30:05').do(clear_chan)
schedule.every().day.at('15:00:05').do(clear_chan)

def schedule_chan():
    #sched_chan()
    while True:
        schedule.run_pending()
        time.sleep(1)

def backtest_chan():
    chan_max.init()
    chan_mid.init()
    chan_min.init()

    st = time.time()
    start = datetime.strptime('2023-01-01 09:30:00', '%Y-%m-%d %H:%M:%S')
    #start = datetime.strptime('2024-12-18 15:00:00', '%Y-%m-%d %H:%M:%S')
    while True:
        flag = int(start.strftime('%y%m%d'))
        if flag >= 230201:
            break
        if not os.path.exists('./datas/m30/%d.csv' % flag):
            start = start + relativedelta(days=1)
            continue
        if not os.path.exists('./datas/m5/%d.csv' % flag):
            start = start + relativedelta(days=1)
            continue
        if not os.path.exists('./datas/m1/%d.csv' % flag):
            start = start + relativedelta(days=1)
            continue
        # 基础日期 历史数据长度 历史数据文件夹
        chan_max.recode(start, 12, './datas/m30')
        chan_mid.recode(start, 6, './datas/m5')
        chan_min.recode(start, 1, './datas/m1')

        for i in range(((11 - 9) + (15 - 13))*2):
            chan_max.input(i + 1, './datas/m30', 30, 3)
            for j in range(6):
                l = (i * 6) + j
                chan_mid.input(l + 1, './datas/m5', 5, 1)
                for k in range(5):
                    l = (i * 6 * 5) + (j * 5) + k
                    # 天数据长度 数据文件夹 数据周期码 通达信周期码
                    count = chan_min.input(l + 1, './datas/m1', 1, 0)
                    chan_min.output(count, l + 1, './datas/m1', 1, 0)
                #l = (i * 6) + j
                #chan_mid.input(l + 1, './datas/m5', 5, 1)
            #chan_max.input(i + 1, './datas/m30', 30, 3)
        print('trade:%d enter:%d %d %d exit:%d %d %d lost:%d profit:%.2f' % (
            chan_min.trade_count, chan_min.enter_count, chan_min.enter_longs, chan_min.enter_shorts,
            chan_min.exit_count, chan_min.exit_longs, chan_min.exit_shorts, chan_min.lost_count, chan_min.profit_count))
        start = start + relativedelta(days=1)
        '''
        i = ((11 - 9) + (15 - 13)) * 2
        chan_max.input(i, './datas/m30', 30, 3)
        i = i * 6
        chan_mid.input(i, './datas/m5', 5, 1)
        i = i * 5
        count = chan_min.input(i, './datas/m1', 1, 0)
        chan_min.output(count, i, './datas/m1', 1, 0)
        break
        '''
    print('耗时: {:.2f}秒'.format(time.time() - st))

rust_chan_dll.RegisterCpyInit()
if __name__ == "__main__":
    #schedule_chan()
    backtest_chan()
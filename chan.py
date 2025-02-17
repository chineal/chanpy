import ctypes
import os

import akshare as ak
import pandas as pd

from glob import glob
from datetime import datetime
from dateutil.relativedelta import relativedelta

current_path = os.getcwd()
os.add_dll_directory(current_path)

rust_chan_dll = ctypes.CDLL('rust_chan.dll')

def init_chan():
    rust_chan_dll.RegisterCpyInit()

def f2p(number):
    return ctypes.pointer(ctypes.c_float(number))

class kline:
    temp_date       = 0
    temp_time       = 0
    temp_close      = 0
    temp_high       = 0
    temp_low        = 0

class chan(kline):
    call_flag       = 0

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

    high_index      = 3
    low_index       = 4
    close_index     = 2

    stroke          = []
    
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

    def temp_init(self):
        self.temp_time  = 0
        self.temp_high  = self.temp_close
        self.temp_low   = self.temp_close

    def temp_update(self, length, path, flag, key, datas: kline):
        if length > 0:
            currents, high, low, close, start = self.currenter(length, path, flag)
        else:
            currents, high, low, close, start = [], 0, 0, 0, 0
        self.temp_time      = self.next(currents, flag)
        self.temp_date      = datas.temp_date
        self.temp_close     = datas.temp_close
        if self.temp_high < datas.temp_high:
            self.temp_high  = datas.temp_high
        if self.temp_low > datas.temp_low:
            self.temp_low   = datas.temp_low
        self.call(key, currents, high, low, close, start)

    def show(self, currents, start):
        dt = []
        data = []
        for item in self.historys:
            dt.append(item[0])
            data.append(item[1:5])
        for i in range(start, len(currents)):
            dt.append(currents[i][0])
            data.append(currents[i][1:5])
        return dt, data, self.stroke
    
    def recode(self, day, prevs, path, key, flag):
        last_month = day - relativedelta(days=30*prevs)
        start = int(last_month.strftime('%y%m%d'))
        end = int(day.strftime('%y%m%d'))
        self.loads(start, end, path)
        rust_chan_dll.RegisterCpyData(key)
        self.call_flag = -99
        self.call(key, [], 0, 0, 0, 0)
        self.update([], self.high_index, self.low_index, self.close_index)
        self.temp_init()

    def input(self, length, path, flag, key):
        currents, high, low, close, start = self.currenter(length, path, flag)
        #if currents[-1][high] != self.temp_high and currents[-1][low] != self.temp_low:
        #    print('error flag:%d high:%.2f/%.2f low:%.2f/%.2f' % (flag, currents[-1][high], self.temp_high, currents[-1][low], self.temp_low))
        self.update(currents, high, low, close)
        self.temp_init()
        return self.call(key, currents, high, low, close, start)

    def currenter(self, length, path, flag):
        high  = self.high_index
        low   = self.low_index
        close = self.close_index
        if length > 0 and self.nexter > 0:
            df = pd.read_csv('%s/%d.csv' % (path, self.nexter), encoding='utf-8')
            currents = df.values.tolist()[:length]
        else:
            high  = 2
            low   = 3
            close = 4
            futures_zh_minute_sina_df = ak.futures_zh_minute_sina(symbol='IF0', period=str(flag))
            currents = futures_zh_minute_sina_df.values.tolist()
            
        start   = 0
        for current in currents:
            dt      = datetime.strptime(current[0], "%Y-%m-%d %H:%M:%S")
            date    = int(dt.strftime('%y%m%d'))
            if date > self.bigest:
                break
            start   += 1

        return currents, high, low, close, start

    def update(self, currents, high, low, close):
        if 0 < len(currents):
            self.temp_high      = currents[-1][high]
            self.temp_low       = currents[-1][low]
            self.temp_close     = currents[-1][close]
            last_date_time      = currents[-1][0]
        else:
            self.temp_high      = self.historys[-1][high]
            self.temp_low       = self.historys[-1][low]
            self.temp_close     = self.historys[-1][close]
            last_date_time      = self.historys[-1][0]
        temp_date_time    = datetime.strptime(last_date_time, "%Y-%m-%d %H:%M:%S")
        self.temp_date    = int(temp_date_time.strftime('%y%m%d'))

    def next(self, currents, flag):
        if 0 < len(currents):
            last_date_time  = currents[-1][0]
        else:
            last_date_time  = self.historys[-1][0]
        temp_date_time      = datetime.strptime(last_date_time, "%Y-%m-%d %H:%M:%S")
        temp_time           = int(temp_date_time.strftime('%H%M%S'))

        temp_time           += flag * 100
        if temp_time > 113000 and temp_time < 130000:
            temp_time       = 130000 + flag * 100
        elif temp_time > 146000:
            temp_time       = 93000 + flag * 100
        if temp_time % 10000 >= 6000:
            temp_time       = int(temp_time / 10000)
            temp_time       += 1
            temp_time       *= 10000
        return temp_time

    def call(self, key, currents, index_high, index_low, index_close, start):
        count = len(self.historys) + (len(currents) - start) + (1 if self.temp_time > 0 else 0)
        buf = ctypes.c_float * count
        out = buf()

        dates   = buf()
        times   = buf()
        highs   = buf()
        lows    = buf()
        closes  = buf()

        i = 0
        for history in self.historys:
            dt          = datetime.strptime(history[0], "%Y-%m-%d %H:%M:%S")
            dates[i]    = int(dt.strftime('%y%m%d'))
            times[i]    = int(dt.strftime('%H%M%S'))
            highs[i]    = history[self.high_index]
            lows[i]     = history[self.low_index]
            closes[i]   = history[self.close_index]
            i += 1
        for j in range(start, len(currents)):
            dt          = datetime.strptime(currents[j][0], "%Y-%m-%d %H:%M:%S")
            dates[i]    = int(dt.strftime('%y%m%d'))
            times[i]    = int(dt.strftime('%H%M%S'))
            highs[i]    = currents[j][index_high]
            lows[i]     = currents[j][index_low]
            closes[i]   = currents[j][index_close]
            i += 1
        if self.temp_time > 0:
            dates[i]    = self.temp_date
            times[i]    = self.temp_time
            '''
            highs[i]    = self.temp_high
            lows[i]     = self.temp_low
            closes[i]   = self.temp_close
            '''
            highs[i]    = 0
            lows[i]     = 0
            closes[i]   = 0

        period  = f2p(key)
        mhs     = buf()
        mls     = buf()
        chs     = buf()
        cls     = buf()
        fracs   = buf()

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
        result = rust_chan_dll.RegisterCpyFunc(4, count, out, f2p(99),  period, f2p(self.call_flag))

        self.call_flag = 0
        self.stroke.clear()
        for frac in fracs:
            self.stroke.append(frac)
        return count
    
    def cur(self, length, path, flag):
        currents, high, low, close, start = self.currenter(length, path, flag)
        return currents, close, start
    
    def output(self, count, length, path, flag, key):
        dates   = []
        times   = []
        closes  = []
        for history in self.historys:
            dt = datetime.strptime(history[0], "%Y-%m-%d %H:%M:%S")
            dates.append(int(dt.strftime('%y%m%d')))
            times.append(int(dt.strftime('%H%M%S')))
            closes.append(history[2])
        
        period  = f2p(key)
        buf     = ctypes.c_float * count

        out     = buf()
        result  = rust_chan_dll.RegisterCpyFunc(5, count, out, f2p(0), f2p(0), period)
        duan    = 0
        for i in range(count):
            if out[i] == 1:
                duan += 1

        ods     = buf()
        open    = 0
        result  = rust_chan_dll.RegisterCpyFunc(7, count, ods, f2p(0), f2p(0), period)
        for i in range(count):
            if ods[i] == 2 or ods[i] == -2:
                open = i

        cds     = buf()
        close   = 0
        result  = rust_chan_dll.RegisterCpyFunc(7, count, cds, f2p(0), f2p(1), period)
        for i in range(count):
            if cds[i] == 4 or cds[i] == -4:
                close = i

        oss     = buf()
        result  = rust_chan_dll.RegisterCpyFunc(6, count, oss, f2p(13), f2p(2), period)

        currents, index_close, start = self.cur(length, path, flag)
        for j in range(start, len(currents)):
            dt = datetime.strptime(currents[j][0], "%Y-%m-%d %H:%M:%S")
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
                        if dates[i] * 1000000 + times[i] == self.openid:
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
                            else:
                                self.exit_shorts += 1
                                self.profit_count += (self.opener - closer)

                        self.openid = 0
                        self.openat = 0
                        self.openly = 0
                        print('lost  at date:%d-%d lates:%d point value:%.2f' %(dates[-1], times[-1], lates, closer))
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
                        else:
                            self.exit_shorts += 1
                            self.profit_count += (self.opener - closer)

                    self.openid = 0
                    self.openat = 0
                    self.openly = 0
                    
                    print('close at date:%d(%d)-%d(%d) lates:%d index:%d %s value:%.2f' %(
                        dates[close],
                        dates[-1],
                        times[close],
                        times[-1],
                        lates,
                        close,
                        'exit  long' if cds[close] < 0 else 'exit  short',
                        closer))
                self.closed = t

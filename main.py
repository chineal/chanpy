import os
#import schedule
import time

from datetime import datetime
from dateutil.relativedelta import relativedelta
from chan import chan, init_chan

#chan_pls = chan()
chan_max = chan()
chan_mid = chan()
chan_min = chan()

def backtest_kline(index):
    currents, high, low, close, start = chan_min.currenter(index + 1, './datas/m1', 1)
    chan_min.update(currents, high, low, close)
    if 0 == (index + 1) % 5:
        chan_mid.input(int((index + 1) / 5), './datas/m5', 5, 1)
    else:
        chan_mid.temp_update(int(index / 5), './datas/m5', 5, 1, chan_min)
    if 0 == (index + 1) % 30:
        chan_max.input(int((index + 1) / 30), './datas/m30', 30, 3)
    else:
        chan_max.temp_update(int(index / 30), './datas/m30', 30, 3, chan_mid)
    count = chan_min.call(0, currents, high, low, close, start)
    chan_min.output(count, index + 1, './datas/m1', 1, 0)

def backtest_once(year, mouth, day, hour, minute, log=0):
    daily = datetime.strptime('20%02d-%02d-%02d' % (year, mouth, day), '%Y-%m-%d')
    flag = int(daily.strftime('%y%m%d'))
    
    if not os.path.exists('./datas/m30/%d.csv' % flag):
        daily += relativedelta(days=1)
        return
    if not os.path.exists('./datas/m5/%d.csv' % flag):
        daily += relativedelta(days=1)
        return
    if not os.path.exists('./datas/m1/%d.csv' % flag):
        daily += relativedelta(days=1)
        return
    
    chan_min.recode(daily, 12*1+1, './datas/m1',    0, 1)
    chan_mid.recode(daily, 12*1+3, './datas/m5',    1, 5)
    chan_max.recode(daily, 12*1+6, './datas/m30',   3, 30)
    chan_min.call_flag = log
    if hour < 12:
        backtest_kline(60*(hour-9)-30+minute-1)
    else:
        backtest_kline(120+60*(hour-13)+minute-1)

def backtest_chan():
    chan_max.init()
    chan_mid.init()
    chan_min.init()

    st = time.time()
    daily = datetime.strptime('2023-01-01', '%Y-%m-%d')
    while True:
        flag = int(daily.strftime('%y%m%d'))
        if flag >= 230501:
            break
        
        if not os.path.exists('./datas/m30/%d.csv' % flag):
            daily += relativedelta(days=1)
            continue
        if not os.path.exists('./datas/m5/%d.csv' % flag):
            daily += relativedelta(days=1)
            continue
        if not os.path.exists('./datas/m1/%d.csv' % flag):
            daily += relativedelta(days=1)
            continue

        # 基础日期 历史数据长度 历史数据文件夹
        chan_min.recode(daily, 12*1+1, './datas/m1',    0, 1)
        chan_mid.recode(daily, 12*1+3, './datas/m5',    1, 5)
        chan_max.recode(daily, 12*1+6, './datas/m30',   3, 30)
        
        end = ((11 - 9) + (15 - 13)) * 60
        for i in range(end - end, end):
            backtest_kline(i)

        print('trade:%d enter:%d %d %d exit:%d %d %d lost:%d profit:%.2f' % (
            chan_min.trade_count, chan_min.enter_count, chan_min.enter_longs, chan_min.enter_shorts,
            chan_min.exit_count, chan_min.exit_longs, chan_min.exit_shorts, chan_min.lost_count, chan_min.profit_count))
        daily += relativedelta(days=1)
    print('耗时: {:.2f}秒'.format(time.time() - st))

def pointest_chan():
    chan_max.init()
    chan_mid.init()
    chan_min.init()
    #250102-135900
    #backtest_once(25, 1, 2, 13, 59)
    #250107-103000
    #backtest_once(25, 1, 7, 10, 30)
    #250107-140000
    #backtest_once(25, 1, 7, 14, 0)
    #backtest_once(25, 1, 13, 9, 31, 1)
    #backtest_once(23, 5, 23, 13, 8, 1)
    #[15:25:27]_recode_30分钟倒数第1笔(时间：241014-133000，点位：3979)，方向：1，于(时间：241016-103300，点位：3817.8)预测反转，当前段：241008-100000
    #backtest_once(24, 10, 16, 10, 33, 1)
    #backtest_once(24, 11, 12, 11, 22, 1)
    backtest_once(24, 4, 29, 11, 30, 1)

init_chan()
if __name__ == "__main__":
    #schedule_chan()
    backtest_chan()
    #pointest_chan()
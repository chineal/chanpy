import os
import schedule
import time

from datetime import datetime
from dateutil.relativedelta import relativedelta
from chan import chan, init_chan

# chan_pls = chan()
# chan_max = chan()
# chan_mid = chan()
chan_min = chan()

def backtest_kline(index):
    currents, high, low, close, start = chan_min.currenter(index + 1, './datas/m1', 1)
    chan_min.update(currents, high, low, close)

    # if 0 == (index + 1) % 5:
    #     chan_mid.input(int((index + 1) / 5), './datas/m5', 5, 1)
    # else:
    #     chan_mid.temp_update(int(index / 5), './datas/m5', 5, 1, chan_min)

    # if 0 == (index + 1) % 30:
    #     chan_max.input(int((index + 1) / 30), './datas/m30', 30, 3)
    # else:
    #     chan_max.temp_update(int(index / 30), './datas/m30', 30, 3, chan_mid)

    count = chan_min.call(0, currents, high, low, close, start)
    chan_min.output(count, index + 1, './datas/m1', 1, 0)

def backtest_once(year, mouth, day, hour, minute, log=0):
    daily = datetime.strptime('20%02d-%02d-%02d' % (year, mouth, day), '%Y-%m-%d')
    flag = int(daily.strftime('%y%m%d'))
    
    # if not os.path.exists('./datas/m30/%d.csv' % flag):
    #     daily += relativedelta(days=1)
    #     return
    # if not os.path.exists('./datas/m5/%d.csv' % flag):
    #     daily += relativedelta(days=1)
    #     return
    if not os.path.exists('./datas/m1/%d.csv' % flag):
        daily += relativedelta(days=1)
        return
    
    chan_min.recode(daily, 12*1+1, './datas/m1',    0, 1)
    # chan_mid.recode(daily, 12*1+3, './datas/m5',    1, 5)
    # chan_max.recode(daily, 12*1+6, './datas/m30',   3, 30)
    chan_min.call_flag = log
    index = 0
    if hour > 12:
        index = 151+135+60*(hour-13)-30+minute-1
    elif hour > 9:
        index = 151+60*(hour-9)+minute-1
    else:
        index = 60*(hour-9)+minute-1
    backtest_kline(index)

def backtest_chan():
    # chan_max.init()
    # chan_mid.init()
    chan_min.init()

    st = time.time()
    daily = datetime.strptime('2025-04-22', '%Y-%m-%d')
    while True:
        flag = int(daily.strftime('%y%m%d'))
        if flag >= 250423:
            break
        
        # if not os.path.exists('./datas/m30/%d.csv' % flag):
        #     daily += relativedelta(days=1)
        #     continue
        # if not os.path.exists('./datas/m5/%d.csv' % flag):
        #     daily += relativedelta(days=1)
        #     continue
        if not os.path.exists('./datas/m1/%d.csv' % flag):
            daily += relativedelta(days=1)
            continue

        # 基础日期 历史数据长度 历史数据文件夹
        chan_min.recode(daily, 12*1+1, './datas/m1',    0, 1)
        # chan_mid.recode(daily, 12*1+3, './datas/m5',  1, 5)
        # chan_max.recode(daily, 12*1+6, './datas/m30', 3, 30)
        
        end = int(((2.5 - 0) + (11 - 9) + (15 - 13) + (24 - 21.5)) * 60 / 1)
        for i in range(0, end):
            # backtest_kline(i)
            chan_min.input(int(i + 1), './datas/m1', 1, 0)
            # chan_mid.input(int(i + 1), './datas/m5', 5, 1)
            # chan_max.input(int(i + 1), './datas/m30', 30, 3)

        print('trade:%d enter:%d %d %d exit:%d %d %d lost:%d profit:%.2f' % (
            chan_min.trade_count, chan_min.enter_count, chan_min.enter_longs, chan_min.enter_shorts,
            chan_min.exit_count, chan_min.exit_longs, chan_min.exit_shorts, chan_min.lost_count, chan_min.profit_count))
        daily += relativedelta(days=1)
    print('耗时: {:.2f}秒'.format(time.time() - st))

def run():
    chan_min.input(0, '', 1, 0)

def sched_chan():
    schedule.every().minute.at(":01").do(run).tag("s_chan")

def schedule_chan():
    chan_min.init()
    daily = datetime.now()
    chan_min.recode(daily, 12*1+1, './datas/m1',    0, 1)
    sched_chan()
    while True:
        schedule.run_pending()
        time.sleep(1)

def pointest_chan():
    # chan_max.init()
    # chan_mid.init()
    chan_min.init()
    # backtest_once(25, 4, 22, 14, 24, 1)
    backtest_once(25, 4, 22, 14, 25, 1)

init_chan()
if __name__ == "__main__":
    # schedule_chan()
    backtest_chan()
    # pointest_chan()
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
'''
def run():
    pass
def sched_chan():
    chan_min.init()
    #chan_min.recode(datetime.now(), 1, './datas/m1', 0, 1)
    chan_min.recode(datetime.now(), 6, './datas/m30', 3, 30)
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
'''

def backtest_kline(index):
    '''
    '''
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
    #1========================================================================================================================================================================
    '''
    currents, high, low, close, start = chan_min.currenter(index + 1, './datas/m5', 5)
    chan_min.update(currents, high, low, close)
    count = chan_min.call(1, currents, high, low, close, start)
    chan_min.output(count, index + 1, './datas/m5', 5, 1)
    '''
    '''
    currents, high, low, close, start = chan_max.currenter(index + 1, './datas/m30', 30)
    chan_max.update(currents, high, low, close)
    count = chan_max.call(3, currents, high, low, close, start)
    chan_max.output(count, index + 1, './datas/m30', 30, 3)
    '''

def backtest_chan():
    chan_max.init()
    chan_mid.init()
    chan_min.init()

    st = time.time()
    #daily = datetime.strptime('2023-01-01', '%Y-%m-%d')
    daily = datetime.strptime('2024-12-16', '%Y-%m-%d')
    while True:
        flag = int(daily.strftime('%y%m%d'))
        if flag >= 250101:
            break
        #2====================================================================================================================================================================
        if not os.path.exists('./datas/m30/%d.csv' % flag):
            daily += relativedelta(days=1)
            continue
        '''
        '''
        '''
        if not os.path.exists('./datas/m5/%d.csv' % flag):
            daily += relativedelta(days=1)
            continue
        '''
        '''
        if not os.path.exists('./datas/m1/%d.csv' % flag):
            daily += relativedelta(days=1)
            continue
        '''

        # 基础日期 历史数据长度 历史数据文件夹
        chan_min.recode(daily, 12*1+1, './datas/m1', 0, 1)
        chan_mid.recode(daily, 12*1+3, './datas/m5', 1, 5)
        chan_max.recode(daily, 12*1+6, './datas/m30', 3, 30)
        #3====================================================================================================================================================================
        #chan_min.recode(daily, 12*0+3, './datas/m5', 1, 5)

        #4====================================================================================================================================================================
        '''
        #end = ((11 - 9) + (15 - 13)) * 2
        end = ((11 - 9) + (15 - 13)) * 12
        #end = ((11 - 9) + (15 - 13)) * 60
        for i in range(end - end, end):
            backtest_kline(i)
        '''
        chan_max.call_flag = 1
        hour = 10
        minute = 30
        if hour < 12:
            backtest_kline(60*(hour-9)-30+minute-1)
        else:
            backtest_kline(120+60*(hour-13)+minute-1)
        return

        print('trade:%d enter:%d %d %d exit:%d %d %d lost:%d profit:%.2f' % (
            chan_min.trade_count, chan_min.enter_count, chan_min.enter_longs, chan_min.enter_shorts,
            chan_min.exit_count, chan_min.exit_longs, chan_min.exit_shorts, chan_min.lost_count, chan_min.profit_count))
        daily += relativedelta(days=1)
    print('耗时: {:.2f}秒'.format(time.time() - st))

init_chan()
if __name__ == "__main__":
    #schedule_chan()
    backtest_chan()
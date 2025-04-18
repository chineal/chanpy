import pandas as pd
from datetime import datetime
from pyecharts import options as opts
from pyecharts.charts import Kline, Line
from chan import chan as Chan

chan = Chan()
data = []
stroke = []

def backtest_kline(index):
    currents, high, low, close, start = chan.currenter(index + 1, './datas/m1', 1)
    chan.update(currents, high, low, close)
    count = chan.call(0, currents, high, low, close, start)
    dt, data, stroke = chan.show(currents, start) # add 2025-2-11
    chan.output(count, index + 1, './datas/m1', 1, 0)
    return dt, data, stroke

def backtest_once(year, mouth, day, hour, minute, log=0):
    daily = datetime.strptime('20%02d-%02d-%02d' % (year, mouth, day), '%Y-%m-%d')
    flag = int(daily.strftime('%y%m%d'))
    chan.recode(daily, 1*1+1, './datas/m1', 0, 1)
    chan.call_flag = log
    if hour < 12:
        return backtest_kline(60*(hour-9)-30+minute-1)
    else:
        return backtest_kline(120+60*(hour-13)+minute-1)

def draw_kline(dt):
    kline_chart = Kline(init_opts=opts.InitOpts(width = "1700px", height = "750px"))
    kline_chart.add_xaxis(dt)
    kline_chart.add_yaxis("kline", data)
    kline_chart.set_global_opts(
        xaxis_opts = opts.AxisOpts(is_scale = True),
        yaxis_opts = opts.AxisOpts(
            is_scale = True,
            splitarea_opts = opts.SplitAreaOpts(
                is_show = True,
                areastyle_opts = opts.AreaStyleOpts(opacity = 1)
            ),
        ),
        datazoom_opts = [opts.DataZoomOpts()],
        title_opts = opts.TitleOpts(title = "Kline-DataZoom-slider"),
    )
    '''
    closes = []
    for d in data:
        closes.append(d[3])
    this_line = Line().add_xaxis(dt).add_yaxis('close', closes, yaxis_index=0)
    this_line.set_series_opts(
        label_opts=opts.LabelOpts(is_show=False),
        linestyle_opts=opts.LineStyleOpts(width=4),
    )
    kline_chart.overlap(this_line)
    '''
    kline_chart.render("kline_datazoom_slider.html")

if __name__ == '__main__':
    chan.init()
    dt, data, stroke = backtest_once(25, 3, 29, 15, 0)
    draw_kline(dt)
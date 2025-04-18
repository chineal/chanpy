import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Kline, Line


def get_file_df():
    file_df = pd.read_csv('./datas/m1/250120.csv')
    file_df.index = pd.to_datetime(file_df['datime'])
    file_df = file_df.iloc[:, :6]
    file_df.columns = ['date', 'open', 'close', 'high', 'low', 'volume']
    file_df = file_df.drop(["date"], axis=1)
    return file_df


def draw_kline(k_dataframe: pd.DataFrame, same_axis_feature: list = None):
    x_value = k_dataframe.index.strftime("%Y-%m-%d %H:%M:%S").tolist()
    kline_chart = Kline(init_opts=opts.InitOpts(width="1700px", height="750px"))
    kline_chart.add_xaxis(xaxis_data=x_value)
    kline_chart.add_yaxis("K线", y_axis=k_dataframe[['open', "close", "low", "high"]].values.tolist())
    kline_chart.set_global_opts(
        xaxis_opts=opts.AxisOpts(is_scale=True),
        yaxis_opts=opts.AxisOpts(
            is_scale=True,
            splitarea_opts=opts.SplitAreaOpts(
                is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)
            ),
        ),
        datazoom_opts=[opts.DataZoomOpts()],
        title_opts=opts.TitleOpts(title="k线图"),
    )
    # 添加同价格的辅助线
    for _index, _feature_name in enumerate(same_axis_feature):
        test = k_dataframe[_feature_name]
        this_line = Line().add_xaxis(x_value).add_yaxis(_feature_name, test, yaxis_index=0)
        this_line.set_series_opts(
            label_opts=opts.LabelOpts(is_show=False),
            linestyle_opts=opts.LineStyleOpts(width=4),
        )
        kline_chart.overlap(this_line)
        break
    kline_chart.render("save_kline.html")


def main():
    file_df: pd.DataFrame = get_file_df()  # 数据源
    file_df['mean_high_close'] = (file_df['high'] + file_df['low']) / 2
    draw_kline(file_df, ["mean_high_close"])


if __name__ == '__main__':
    main()
from django.shortcuts import render, redirect, HttpResponse
from .models import China, ForeignArea
from .forms import ChinaForm, ForeignAreaForm
from django.contrib.auth.decorators import login_required
from jinja2 import Environment, FileSystemLoader
from pyecharts.globals import CurrentConfig
import pandas as pd
from pyecharts.charts import Map, Pie, WordCloud, Line, Page
from pyecharts.components import Table
from pyecharts import options as opts
import pymysql
import time
import datetime
import json
import re
import warnings

warnings.simplefilter('ignore', category=UserWarning)

CurrentConfig.GLOBAL_ENV = Environment(loader=FileSystemLoader("./frontpage/templates"))


@login_required
def china_change(request, data_id):
    """中国疫情数据修改"""
    china_data = China.objects.get(id=data_id)
    if request.method != 'POST':
        # 未提交数据：创建一个空表单，且使用旧条目内容填充表单
        form = ChinaForm(instance=china_data)
    else:
        # 对POST提交的数据进行处理：在旧条目(instance=china_data)上，覆盖上新条目的内容(data=request.POST)
        form = ChinaForm(instance=china_data, data=request.POST)
        if form.is_valid():
            # 用该表单对象来执行数据库的存储操作
            form.save()
            # 用户填入的表单数据存入数据库后，重定向页面至查询页
            return redirect('frontpage:query')
    # 显示空表单或指出表单数据无效
    context = {'china_data': china_data, 'form': form}
    # 调用新建条目页面的模板，并传入上下文字典
    return render(request, 'frontpage/china_change.html', context)


@login_required
def foreign_change(request, data_id):
    """全球疫情数据修改"""
    foreign_data = ForeignArea.objects.get(id=data_id)
    if request.method != 'POST':
        form = ForeignAreaForm(instance=foreign_data)
    else:
        form = ForeignAreaForm(instance=foreign_data, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('frontpage:query')
    context = {'foreign_data': foreign_data, 'form': form}
    return render(request, 'frontpage/foreign_change.html', context)


@login_required
def query(request):
    """查询数据"""
    if request.method != 'POST':
        return render(request, 'frontpage/query.html')
    else:
        data = dict(request.POST)
        area = data['area'][0]
        date = f"{data['year'][0]}-{data['month'][0]}-{data['day'][0]}"
        if area == '中国':
            datas = China.objects.filter(date=date).order_by('total').reverse()
        elif area == '全球':
            datas = ForeignArea.objects.filter(date=date).order_by('total').reverse()
        context = {'datas': datas, 'area': area, 'date': date}
        return render(request, 'frontpage/datas.html', context=context)


def index(request):
    """数据可视化主页"""
    
    """生成数据集"""
    # 连接数据库
    con = pymysql.connect(host='127.0.0.1', user='root', passwd='root123', db='百度疫情')

    t = time.time()  # 本地时间戳
    local_time = time.localtime(t)
    date = time.strftime('%Y-%m-%d', local_time)
    hour = time.strftime('%H', local_time)
    if int(hour) < 10:  # 若此刻处于今日的10点钟前，则将日期推前10小时
        date = time.strftime('%Y-%m-%d', time.localtime(t-36000))
    # 获取绘制table_china，map，line，pie所需的今日数据
    df_china = pd.read_sql(f"select area,newly,total,cure,dead from frontpage_china where date = '{date}'",
                           con=con)  # 获取DataFrame
    china_data = df_china.values.tolist()  # DataFrame转换为列表：[['上海', 3241, 27078, 9288, 7], ...]
    china_data.sort(key=lambda x: x[1], reverse=True)

    # 获取绘制line_week所需的数据
    date_y, date_m, date_d = [int(x) for x in date.split('-')]
    begin = datetime.date(date_y, date_m, date_d)  # 创建datetime的日期对象
    week_date = [str(begin - datetime.timedelta(days=i)) for i in range(7)]  # 近一周的日期列表
    week_1, week_2, week_3, week_4, week_5, week_6, week_7 = week_date
    df_china_week = pd.read_sql(  # 中国近一周疫情DataFrame
        f"select area,newly,total,cure,dead from frontpage_china where date in ('{week_1}', '{week_2}', '{week_3}', '{week_4}', '{week_5}', '{week_6}', '{week_7}')"
        , con=con)  # 获取DataFrame
    week_data = df_china_week.values.tolist()  # DataFrame转换为列表
    area_list = [x[0] for x in week_data]  # 获取地区列表
    area_list = list(set(area_list))  # 去重
    china_week_data = list()
    for i in area_list:  # 倒序
        a = 0
        for j in week_data:
            if i == j[0]:
                a += j[1]
        china_week_data.append([i, a])
    china_week_data.sort(key=lambda x: x[1], reverse=True)
    
    # 获取绘制table_global，wordcloud所需的数据
    df_foreign = pd.read_sql(f"select country,newly,total,cure,dead from frontpage_foreignarea where date = '{date}'",
                             con=con)  # 通过sql语句获取到所需的DataFrame
    # [['美国', 44139, 82309113, 80166281, 1015441], ...]
    foreign_data = df_foreign.values.tolist()  # DataFrame转换为列表
    
    def line_week():
        """周折线图数据集： [['上海', 5661], ...]"""
        line_week = (
            Line(
                init_opts=opts.InitOpts(
                    width='700px',
                    height='400px',  # 图表的宽与高
                )
            )
            .add_xaxis(xaxis_data=[x[0] for x in china_week_data])  # x轴数据集
            .add_yaxis(
                '本周内的新增确诊',  # 数据集名
                [x[1] for x in china_week_data],  # y轴数据集
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title='周确诊折线图',  # 标题
                    pos_right='90',  # 标题离画布左边，与顶边的相对距离
                    pos_top='40',  # 置顶位置
                    title_textstyle_opts=opts.TextStyleOpts(
                        font_size=24,  # 标题字号
                    ),
                ),
                legend_opts=opts.LegendOpts(is_show=False),  # 是否显示图例，默认为True
                xaxis_opts=opts.AxisOpts(type_='category'),  # x轴数据类型
                datazoom_opts=opts.DataZoomOpts(
                    is_show=True,  # 显示滑块
                    range_start=0,  # 滑块的起始范围(0-100，表示0%-100%)
                    range_end=30,
                )
            )
        )
        return line_week
    
    def wordcloud():
        """全球词云图"""
        wordcloud_data = [[x[0], x[2]] for x in foreign_data]
        wordcloud = (
            WordCloud(
                init_opts=opts.InitOpts(
                    width='600px',
                    height='360px',  # 图表的宽与高
                )
            )
            .add(
                '',
                wordcloud_data,  # 词云数据集
                word_size_range=[10, 150],  # 设置词云中文字的最小与最大尺寸
                textstyle_opts=opts.TextStyleOpts(font_family='cursive'),  # 设置字体
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title='',  # 标题
                    pos_left='500',  # 标题离画布左边，与顶边的相对距离
                    title_textstyle_opts=opts.TextStyleOpts(
                        font_size=28,  # 标题字号
                    ),
                )
            )
        )
        return wordcloud
    
    def table_global():
        """全球各国的当日数据表格"""
        headers = ['国家', '新增确诊', '累计确诊', '累计治愈', '累计死亡']
        attributes = {"class": "fl-table"}
        table_global = (
            Table()
            .add(headers, foreign_data, attributes)
            .set_global_opts(title_opts=opts.ComponentTitleOpts(
                title='今日疫情数据：全球'),
            )
        )
        return table_global
    
    def table_china():
        """中国各省的当日数据表格"""
        headers = ['各省份/ 直辖市/ 自治区', '新增确诊', '新增无症状', '累计确诊', '风险地区']
        attributes = {"class": "fl-table"}
        table_china = (
            Table()
            .add(headers, china_data, attributes)
            .set_global_opts(title_opts=opts.ComponentTitleOpts(
                title='今日疫情数据：中国'),
            )
        )
        return table_china
    
    def pie():
        """饼图数据集(前九名与其他)"""
        pie_data = [[x[0], x[3]] for x in china_data]  # china_data(旧)：[['上海', 新增3241, 累计27078, 治愈9288, 死亡7], ...]
        pie_data.sort(key=lambda x: x[1], reverse=True)
        pie_9 = pie_data[:9]
        pie_other = ['其它省份', sum([x[1] for x in pie_data[9:]])]
        pie_9.append(pie_other)
        pie = (
            Pie(
                init_opts=opts.InitOpts(
                    width='600px',
                    height='300px',  # 图表的宽与高
                )
            )
            .add(  # 饼图以二维列表作为数据集，其中的每个列表包含2个元素，图例默认为“x”的各元素
                '累计确诊',  # 数据集名
                pie_9,  # 数据集
                radius=['10%', '75%'],
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title='中国各省饼图',  # 标题
                    title_textstyle_opts=opts.TextStyleOpts(
                        font_size=24,  # 标题字号
                    ),
                ),
                legend_opts=opts.LegendOpts(orient='vertical', pos_top='12%', pos_left='0%'),  # 图例设置
                tooltip_opts=opts.TooltipOpts(formatter="{a}：{c}")  # 格式化浮窗：{a} 数据集名，{b} x值，{c} y值
            )
            .set_series_opts(label_opts=opts.LabelOpts(is_show=True))  # 图形标签字符的设置
        )
        return pie
    
    def line():
        """日折线图数据集(数据源是按新增确诊数降序排列的)： [['上海', 3241], ...]"""
        line_data = [[x[0], x[1]] for x in china_data]  # china_data(旧)：[['上海', 新增3241, 累计27078, 治愈9288, 死亡7], ...]
        line = (
            Line(
                init_opts=opts.InitOpts(
                    width='700px',
                    height='400px',  # 图表的宽与高
                )
            )
            .add_xaxis(xaxis_data=[x[0] for x in line_data])  # x轴数据集
            .add_yaxis(
                '新增确诊',  # 数据集名
                [x[1] for x in line_data],  # y轴数据集
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title='日确诊折线图',  # 标题
                    pos_right='90',  # 标题离画布左边，与顶边的相对距离
                    pos_top='40',  # 置顶位置
                    title_textstyle_opts=opts.TextStyleOpts(
                        font_size=24,  # 标题字号
                    ),
                ),
                legend_opts=opts.LegendOpts(is_show=False),  # 是否显示图例，默认为True
                xaxis_opts=opts.AxisOpts(type_='category'),  # x轴数据类型
                datazoom_opts=opts.DataZoomOpts(
                    is_show=True,  # 显示滑块
                    range_start=0,  # 滑块的起始范围(0-100，表示0%-100%)
                    range_end=30,
                )
            )
        )
        return line
    
    def map():
        """地图数据集： [['上海', 27078], ...]"""
        map_data = [[x[0], x[1]] for x in china_week_data]  # china_data(旧)：[['上海', 新增3241, 累计27078, 治愈9288, 死亡7], ...]
        map = (
            Map(
                init_opts=opts.InitOpts(
                    width='600px',
                    height='800px',  # 图表的宽与高
                )
            )
            .add(
                series_name='',  # 数据集名称
                data_pair=map_data,  # 数据集
                maptype='china',
                is_roam=True,  # 关闭鼠标缩放和平移漫游
                is_map_symbol_show=False,  # 是否显示地理标记(小红点)
                label_opts=opts.LabelOpts(
                    is_show=False,  # 是否显示地名数据标签
                ),
                itemstyle_opts={
                    "emphasis": {  # 鼠标滑过时的强调样式
                        "areaColor": "rgba(255,255,0, 1)",  # 区域强调色彩
                    },
                },
            )
            .set_global_opts(  # 全局设置
                title_opts=opts.TitleOpts(  # 标题
                    title='中国疫情热力图(周确诊)',  # 标题
                    pos_left='400',  # 标题离画布左，上的相对距离
                    pos_top='120',  # 置顶位置
                    title_textstyle_opts=opts.TextStyleOpts(
                        font_size=28,  # 标题字号
                    ),
                ),
                legend_opts=opts.LegendOpts(is_show=False),  # 是否显示图例，默认为True
                tooltip_opts=opts.TooltipOpts(
                    is_show=True,  # 显示浮窗
                    formatter="{b}：{c}",  # {b} x值，{c} y值
                    textstyle_opts=opts.TextStyleOpts(font_size=16)  # 文本格式，详见：series_options
                ),
                visualmap_opts=opts.VisualMapOpts(  # 视觉组件设置
                    is_show=False,  # 不显示组件
                    max_=100,  # 最大值5000
                    pos_top=50,  # 置顶位置
                    range_color=[  # 设置色彩过渡的列表
                        "white",
                        "lightblue",
                        "orange",
                        "red",
                    ],
                )
            )
        )
        return map
    
    def page_layout():
        """图表布局"""
        
        # 首次生成图表后手动排版，Save Config
        page = Page(layout=Page.DraggablePageLayout)  # 可拖动布局
        page.add(
            pie(),
            line(),
            line_week(),
            wordcloud(),
            table_global(),
            table_china(),
            map(),
        )
        page.render('./frontpage/templates/组合图表(原始).html')  # 生成page布局图
        
        # 移花接木
        with open('./frontpage/templates/组合图表(原始).html', 'r', encoding='utf-8') as f:
            html = f.read()
        pattern = re.compile('<div id="(.*?)"')
        id_list = re.findall(pattern, html)
        # chart_config是page.add(不能改动图表添加的顺序)中按顺序生成的7个图表
        chart_config = [{"cid": "f266c787a1ef4457a0b4ed35a49549b2", "width": "600px", "height": "300px", "top": "75px", "left": "19px"},
                        {"cid": "7ff76c4741214b9797ba9e047851bb1f", "width": "984px", "height": "239px", "top": "750px", "left": "-41px"},
                        {"cid": "20df892350fe4c72bff69c2b79af1067", "width": "998px", "height": "239px", "top": "750px", "left": "855px"},
                        {"cid": "94ecafbee33d4793b7781c7a739fb049", "width": "600px", "height": "360px", "top": "32px", "left": "1229px"},
                        {"cid": "9f010cfe40544b3788fc01db5e5c011a", "width": "542px", "height": "414px", "top": "365px", "left": "1241px"},
                        {"cid": "68fd6f87c4794e9aaba21cefc067a956", "width": "542px", "height": "414px", "top": "365px", "left": "4px"},
                        {"cid": "cf99d071e3d449bd830e86ea220a61d7", "width": "1000px", "height": "800px", "top": "-16px", "left": "384px"}]
        # 完成cid的移花接木
        for a, b in zip(chart_config, id_list):
            a['cid'] = b
        # 生成cid与新生成的 组合图表(已排版).html 中的id相匹配的chart_config.json
        with open("./frontpage/templates/chart_config.json", 'w', encoding='utf-8') as f:
            json.dump(chart_config, f, ensure_ascii=False)
        
        # 用经手动排版的组合图表文件，及 Save Config 后生成的 chart_config.json 文件来组合生成手动排版的组合图表。
        Page.save_resize_html(
            "./frontpage/templates/组合图表(原始).html",
            cfg_file="./frontpage/templates/chart_config.json",
            dest="./frontpage/templates/组合图表(已排版).html"
        )
    
    """生成Pyecharts的Page图表"""
    page_layout()
    # 读取本地已排版好的可视化源码，匹配出其中用于渲染图表的源码部分
    with open("./frontpage/templates/组合图表(已排版).html", 'r', encoding='utf-8') as f:
        html = f.read()
    chart = re.findall("<body>(.*)</body>", html, re.DOTALL)[0]
    # 将图表的源码传入数据可视化主页的模板中
    context = {'chart': chart}
    return render(request, 'frontpage/index.html', context)

# -*- coding:utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
from lxml import etree
import pymysql
from loguru import logger

"""
    分析：
        1.数据源：https://voice.baidu.com/act/newpneumonia/newpneumonia/
          当日中国各省与全球各国家(Tab(table...))的：新增确诊，累计确诊，累计治愈，累计死亡表格
        2.selenium爬取该页面需用于可视化的数据，存入MySQL中(当日仅第一次运行爬虫时爬取)
        3.数据可视化页面：中国各省(自治区,直辖市)累计确诊热力图，
                       日确诊折线图(降序)，周确诊折线图(降序)，
                       累计确诊饼图(前九名与其他)
                       全球词云图(国家名称，累计确诊数)             
        4.登录查询及修改数据
"""


def get_data():
    # 目标网页
    url = 'https://voice.baidu.com/act/newpneumonia/newpneumonia/'

    # 创建Chrome的设置选项
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    options.add_argument('user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47"')
    options.add_argument('--disable-gpu')
    # 自动管理Chrome驱动
    options.binary_location = r"C:\Users\Chromium\Application\Chromium.exe"
    # 注意：需下载与win11系统安装的Chrome浏览器版本相匹配的webdriver，Windows11目前使用Chrome驱动自动管理会报错
    # bro = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    bro = webdriver.Chrome('chromedriver.exe', options=options)

    # 获取今天日期(直接用time.gmtime()有时差)
    t = time.time()  # 本地时间
    local_time = time.localtime(t)
    date = time.strftime('%Y-%m-%d', local_time)
    with open('check_date.txt', encoding='utf-8') as f:
        dates = f.readlines()
    dates = [x.strip() for x in dates]
    hour = time.strftime('%H', local_time)
    # 检查爬虫运行的时间段
    if int(hour) < 10:
        print('请于每日10点后运行爬虫，以确保爬取到当日更新较为完整的数据...')
        exit()

    if date in dates:
        print('今日的数据已经爬取完毕，请等到明天再继续运行爬虫...')
        exit()
    dates.append(date)
    # 连接数据库
    con = pymysql.connect(host='127.0.0.1', user='root', passwd='root', db='百度疫情')
    cur = con.cursor()  # 创建操作光标
    # 打开页面
    bro.get(url)
    # 展开中国个各省份与全球各个国家的数据节点(后续一部分的源码被隐藏在::after中，需点击展开才会显示在页面中)
    unfold = bro.find_element(By.XPATH, '//div[@id="nationTable"]/div')
    unfold.click()
    unfold = bro.find_element(By.XPATH, '//div[@id="foreignTable"]/div')
    unfold.click()
    text = bro.page_source  # 获取页面源码
    tree = etree.HTML(text)  # 创建etree实例
    # 解析：中国各省份的数据节点
    trs = tree.xpath('//div[@id="nationTable"]//tbody/tr')
    # 解析：地区，新增确诊，新增无症状，累计确诊，风险地区
    for tr in trs:  # 遍历所有节点
        area = tr.xpath('./td[1]//text()')[0]  # 地区
        newly = tr.xpath('./td[2]//text()')[0]  # 新增确诊
        # if newly == '-':
        #     newly = '0'
        total = tr.xpath('./td[3]//text()')[0]  # 累计确诊 —>新增无症状
        if total == '-':
            total = '0'
        cure = tr.xpath('./td[4]//text()')[0]  # 累计治愈 —>累计确诊
        # if cure == '-':
        #     cure = '0'
        dead = tr.xpath('./td[5]//text()')[0]  # 累计死亡 —>风险地区
        # if dead == '-':
        #     dead = '0'
        # 创建需插入数据库的数据列表(一条记录)
        params = [date, area, newly, total, cure, dead]
        # 编写插入数据到用户表的sql语句
        insert_sql = '''
               INSERT INTO frontpage_china (date, area, newly, total, cure, dead) VALUES(%s, %s, %s, %s, %s, %s)
               '''
        cur.execute(insert_sql, tuple(params))  # 在该光标上执行sql语句
        con.commit()  # 提交，保存到数据库
        logger.debug(f'storage {area} {newly} {total} {cure} {dead}')
    # 解析：全球各国家的数据节点(部分国家的class为空，所以通过更精准的路径去解析tr节点)
    trs = tree.xpath('//div[@id="foreignTable"]//tbody//tbody/tr')
    # 解析：地区，新增确诊，累计确诊，累计治愈，累计死亡
    for tr in trs:  # 遍历所有节点
        foreign_area = tr.xpath('./td[1]//text()')[0]
        foreign_newly = tr.xpath('./td[2]//text()')[0]
        if foreign_newly == '-':
            foreign_newly = '0'
        foreign_total = tr.xpath('./td[3]//text()')[0]
        # if foreign_total == '-':
        #     foreign_total = '0'
        foreign_cure = tr.xpath('./td[4]//text()')[0]
        # if foreign_cure == '-':
        #     foreign_cure = '0'
        foreign_dead = tr.xpath('./td[5]//text()')[0]
        # if foreign_dead == '-':
        #     foreign_dead = '0'
        # 创建需插入数据库的数据列表
        params = [date, foreign_area, foreign_newly, foreign_total, foreign_cure, foreign_dead]
        # 编写插入数据到用户表的sql语句
        insert_sql = '''
               INSERT INTO frontpage_foreignarea (date, country, newly, total, cure, dead) VALUES(%s, %s, %s, %s, %s, %s)
               '''
        cur.execute(insert_sql, tuple(params))  # 在该光标上执行sql语句
        con.commit()  # 提交，保存到数据库
        logger.debug(f'storage {foreign_area} {foreign_newly} {foreign_total} {foreign_cure} {foreign_dead}')
    # 爬取完毕，退出浏览器
    bro.quit()
    # 更新日期记录入本地文本中
    with open('check_date.txt', 'w', encoding='utf-8') as f:
        f.writelines([x+'\n' for x in dates])
        

if __name__ == '__main__':
    get_data()  # 运行爬虫
    

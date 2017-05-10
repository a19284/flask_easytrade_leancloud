# coding: utf-8

from leancloud import Engine
from leancloud import LeanEngineError
import time
from app import app
import sqlite3API
import auto_trader
import easyquotation
from send_mail import send_mail

import pandas as pd
from pandas.compat import StringIO
try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

engine = Engine(app)

@engine.define
def hello(**params):
    if 'name' in params:
        return 'Hello, {}!'.format(params['name'])
    else:
        return 'Hello, LeanCloud!'
    
@engine.define
def getHangqingFromQQ():
    q = easyquotation.use('qq')

    #取上市300天内的最小流通市值 top 40
    dic,stock_list = gettimeToMarket()

    #取得最新行情 from qq
    stockinfo,stockinfo_zhangting = q.stocks(stock_list)

    #按流通市值排序
#    temp = sorted(stockinfo.items(), key=lambda d:d[1]['流通市值'])

    #最小流通市值取得
    min_liutong = min(stockinfo.items(), key=lambda d:d[1]['流通市值'])[1]
    
    #get Position
    dic_position = auto_trader.getPosition()
    
#    if key in dic_position.keys():
        
    #计算流通市值差
    for key,value in stockinfo.items():
        try:
            if key in dic_position.keys():
                #市值差 （流通市值/最小流通市值）-1
                stockinfo[key]['cha'] = str(round((float(stockinfo[key]['流通市值'])/float(min_liutong['流通市值']) - 1)*100,2)) + '%'
                #去损耗市值差  （流通市值*现价/买1价）/（最小流通市值*现价/卖1价）-1
                liutong_sunhao = stockinfo[key]['流通市值']*stockinfo[key]['bid1']/stockinfo[key]['now']
                min_liutong_sunhao = min_liutong['流通市值']*min_liutong['ask1']/min_liutong['now']
                stockinfo[key]['cha_sunhao'] = str(round((liutong_sunhao/min_liutong_sunhao - 1)*100,2)) + '%'

                #该股为持仓股时，判断是否需要调仓
    #            if key in dic_position.keys():
                auto_trader.autoTrader(stockinfo[key],min_liutong,round((liutong_sunhao/min_liutong_sunhao - 1)*100,3))
        except Exception as e:
            print (e)
        
#从本地sqlite取得上市日期
def gettimeToMarket():

    conn = sqlite3API.get_conn('stock.db')
    sql_tid='''
        select stock_info.code,stock_info.timeToMarket from liutong_from_qq 
        inner join stock_info on
        liutong_from_qq.code = stock_info.code
        where liutong_from_qq.liutong<13 and substr(liutong_from_qq.code,1,1) != '3' 
        and substr(stock_info.timeToMarket,1,4) || '-' || substr(stock_info.timeToMarket,5,2) || '-' || substr(stock_info.timeToMarket,7,2) > date('now','-270 days')
        order by liutong_from_qq.liutong 
        limit 40;
        '''
    #union all XXX 持仓股
        
    info_tid=sqlite3API.fetchmany(conn,sql_tid)
    dic = dict()
    stock_list=[]
    for info_temp in info_tid:
        dic[info_temp[0]] = str(info_temp[1])
        stock_list.append(info_temp[0])
    
    return dic,stock_list
    
@engine.define
def getPositionAndBuyIPO():
    try:
        user = auto_trader.getUser()
        #position
        data = auto_trader.insertPosition(user.position)
        time.sleep(2)
        #getIpo
        df_today_ipo, df_ipo_limit = user.get_ipo_info()
        result_mail = ''
        for i in range(len(df_today_ipo)):
            code = df_today_ipo.ix[i]['代码']
            price = df_today_ipo.ix[i]['价格']
            amount = df_today_ipo.ix[i]['账户额度']
            result = user.buy(code,price,amount=amount)
            result_mail += '***<br>\r\n buy IPO:%s,%s,%s,%s' % (code,price,amount,str(result))
        send_mail('Position and IPO',str(data) + result_mail)
    except Exception as e :
        print(str(e))
        send_mail('[error] Position and IPO ',str(e))

@engine.define
def getAllStockInfo():
    df = get_stock_basics()
    conn = sqlite3API.get_conn('stock.db')
    df.to_sql('stock_info',con=conn,flavor='sqlite', if_exists='replace')
    
    #取得流通市值
    getLiutong_from_qq()
    
#get_stock_basics
def get_stock_basics():
    """
        获取沪深上市公司基本情况
    Return
    --------
    DataFrame
               code,代码
               name,名称
               industry,细分行业
               area,地区
               pe,市盈率
               outstanding,流通股本
               totals,总股本(万)
               totalAssets,总资产(万)
               liquidAssets,流动资产
               fixedAssets,固定资产
               reserved,公积金
               reservedPerShare,每股公积金
               eps,每股收益
               bvps,每股净资
               pb,市净率
               timeToMarket,上市日期
    """
    ALL_STOCK_BASICS_FILE = 'http://218.244.146.57/static/all.csv'
    request = Request(ALL_STOCK_BASICS_FILE)
    text = urlopen(request, timeout=10).read()
    text = text.decode('GBK')
    text = text.replace('--', '')
    df = pd.read_csv(StringIO(text), dtype={'code':'object'})
    df = df.set_index('code')
    return df

def getCixinCode():
    conn = sqlite3API.get_conn('stock.db')

    sql_tid='''
        select code from stock_info 
        where substr(stock_info.timeToMarket,1,4) || '-' || substr(stock_info.timeToMarket,5,2) || '-' || substr(stock_info.timeToMarket,7,2) > date('now','-300 days') 
        and substr(code,1,1) != '3' ;
        '''
    info_tid=sqlite3API.fetchmany(conn,sql_tid)
    stock_list=[]
    for info_temp in info_tid:
        stock_list.append(info_temp[0])
    
    return stock_list     

def getLiutong_from_qq():
    q = easyquotation.use('qq')

    #取上市300天内的股票
    stock_list = getCixinCode()
    stockinfo,stockinfo_zhangting = q.stocks(stock_list)
    data = []
    
    for key,value in stockinfo.items():
        try:
            infoLiutong = (stockinfo[key]['code'],stockinfo[key]['流通市值'])
            data.append(infoLiutong)

        except Exception as e:
            print(e)
            
    for key,value in stockinfo_zhangting.items():
        try:
            infoLiutong = (stockinfo_zhangting[key]['code'],stockinfo_zhangting[key]['流通市值'])
            data.append(infoLiutong)

        except Exception as e:
            print(e)
    #sql_truncat = 'truncat table liutong_from_qq'
    sql = 'insert into liutong_from_qq values(?,?)'
    conn = sqlite3API.get_conn('stock.db')
    #sqlite3API.save(conn,sql_truncat,data)
    sqlite3API.truncate(conn,'liutong_from_qq')

    sqlite3API.save(conn,sql,data)
    print('getLiutong_from_qq OK!')
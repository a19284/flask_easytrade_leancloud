# coding: utf-8

from leancloud import Engine
from leancloud import LeanEngineError
#import requests
from app import app
import sqlite3API
import auto_trader
import easyquotation
from send_mail import send_mail

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
def sendmailtest():
    send_mail('测试','leancloud cloud测试')
# coding: utf-8

from leancloud import Engine
from leancloud import LeanEngineError
import time
from app import app
import sqlite3API
import auto_trader
import easyquotation
from send_mail import send_mail
import leanDBAccess 

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
    dic,stock_list_300 = gettimeToMarket()
    #持仓股取得
    dic_position = auto_trader.getPosition()
    #获取对象
    stock_list = list(set(stock_list_300)|set(dic_position.keys()))

    #取得最新行情 from qq
    stockinfo,stockinfo_zhangting = q.stocks(stock_list)

    #按流通市值排序
    temp = sorted(stockinfo.items(), key=lambda d:d[1]['流通市值'])
    #非持仓 最小流通市值取得
    min_liutong_trade = None
    #print(temp)
    for key,value in temp:
        if checkExistsCode(key)==False:
            min_liutong_trade = value
            print('min_liutong_trade',min_liutong_trade['code'],min_liutong_trade['name'],min_liutong_trade['流通市值'])
            break
    
    #取得最大持仓
    max_chicang_liutong_trade = getMaxChicangLiutong(stockinfo,dic_position.keys())

    #该股为持仓股时，判断是否需要调仓
    if max_chicang_liutong_trade and min_liutong_trade:
        print ('max_chicang_liutong_trade',max_chicang_liutong_trade['code'],max_chicang_liutong_trade['name'],max_chicang_liutong_trade['流通市值'])
        
        max_liutong_sunhao = max_chicang_liutong_trade['流通市值']*max_chicang_liutong_trade['bid1']/max_chicang_liutong_trade['now']
        min_liutong_sunhao = min_liutong_trade['流通市值']*min_liutong_trade['ask1']/min_liutong_trade['now']
        max_min_cha_suohao = round((max_liutong_sunhao/min_liutong_sunhao - 1)*100,3)
        #max_min_cha = str(round((max_chicang_liutong_trade['流通市值']/min_liutong_trade['流通市值'] - 1)*100,2)) + '%'
    #    print(max_min_cha_suohao)
        auto_trader.autoTrader(max_chicang_liutong_trade,min_liutong_trade,max_min_cha_suohao)
'''
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
'''        
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
def getPosition():
    try:
        user = auto_trader.getUser()
        #position
        data = auto_trader.insertPosition(user.position)
        send_mail('Position ',str(data))
        print(str(data))
    except Exception as e :
        print(str(e))
        send_mail('[error] Position ',str(e))

@engine.define
def buyIPO():
    try:
        user = auto_trader.getUser()
        #getIpo
        df_today_ipo,df_ipo_limit = user.get_ipo_info()
        result_mail = ''
        for i in range(len(df_today_ipo)):
            code = df_today_ipo.ix[i]['代码']
            price = df_today_ipo.ix[i]['价格']
            amount = df_today_ipo.ix[i]['账户额度']
            result = user.buy(code,price,amount=amount)
            result_mail += '\r\n[%s]buy IPO:%s,%s,%s,%s' % (str(i+1),code,price,amount,str(result))
            time.sleep(2)
            
        if result_mail:
            send_mail('buyIPO',result_mail)
            print(result_mail)
        else:
            #none ipo
            print('today none IPO!')
            
        #资金状况
        leanDBAccess.saveBalanceLeanCloud(user.balance)
        time.sleep(2)
        #持仓
        auto_trader.insertPosition(user.position)
#        time.sleep(2)
    except Exception as e :
        print(str(e))
        send_mail('[error] buyIPO ',str(e))

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
#    ALL_STOCK_BASICS_FILE = 'http://218.244.146.57/static/all.csv'
    ALL_STOCK_BASICS_FILE = 'http://file.tushare.org/tsdata/all.csv'
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


#判断股票是否持仓
def checkExistsCode(code):
    conn = sqlite3API.get_conn('stock.db')

    sql_tid='''
        select code from chicang 
        where code = '%s' ;
        '''
    info_tid=sqlite3API.fetchmany(conn,sql_tid % code)
    if info_tid and len(info_tid)>0:
        return True
    else:
        return False
        
#取得可用股份数
def getKeyongGufen(code):
    conn = sqlite3API.get_conn('stock.db')

    sql_tid='''
        select gufen_keyong from chicang 
        where code = '%s' ;
        '''
    info_tid=sqlite3API.fetchmany(conn,sql_tid % code)
    if info_tid and len(info_tid)>0:
        return info_tid[0][0]
    else:
        return 0

#取得持仓股中，流通市值最大的且可交易的股票
def getMaxChicangLiutong(stockinfo,listCode):
    dicMaxLiutong = dict()
    liutong = 0.0
    for code in listCode:
        if getKeyongGufen(code)>0 and stockinfo[code]['流通市值']>liutong:
            liutong = stockinfo[code]['流通市值']
            dicMaxLiutong = stockinfo[code]
    return dicMaxLiutong

if __name__ == '__mian__':
#    getHangqingFromQQ()
    pass
from flask import render_template
from flask import Flask
from flask import request
#import requests
import easyquotation
import datetime
#import sqlite3 as lite
import sqlite3API
import auto_trader
import leanDBAccess 
from leancloud import cloudfunc

app = Flask(__name__)

@app.route('/')
def hello(name=None):
#    b=[{'参考市值': 21642.0,
#      '可用资金': 28494.21,
#      '币种': '0',
#      '总资产': 50136.21,
#      '股份参考盈亏': -90.21,
#      '资金余额': 28494.21,
#      '资金帐号': 'xxx'}]
#    p=[{'买入冻结': 0,
#      '交易市场': '沪A',
#      '卖出冻结': '0',
#      '参考市价': 4.71,
#      '参考市值': 10362.0,
#      '参考成本价': 4.672,
#      '参考盈亏': 82.79,
#      '当前持仓': 2200,
#      '盈亏比例(%)': '0.81%',
#      '股东代码': 'xxx',
#      '股份余额': 2200,
#      '股份可用': 2200,
#      '证券代码': '601398',
#      '证券名称': '工商银行'}]
#    leanDBAccess.savePositionLeanCloud(p)
#    leanDBAccess.saveBalanceLeanCloud(b)
#    
#    t={'PB': 6.36, 'high_2': 37.02, 'bid3_volume': 2700, 'ask4_volume': 5100, 'code': '603991', 'bid5_volume': 500, 'ipo_date_num_css': 0, '损耗': '0.03%', 'bid1_num': 5.14, '涨跌(%)': '2.23%', '成交量(手)': 1073800, '价格/成交量(手)/成交额': '36.72/10738/39058147', 'bid1_num_css': '', 'bid2_volume': 2400, 'datetime': ' 15:10:57', 'cha_sunhao': 0, 'bid1_volume': 1400, 'low_2': 35.56, 'ask3': 36.75, 'ask1': 36.73, 'unknown': '', 'ask1_num_css': '', 'ask_volume': 499700.0, 'close': 35.94, 'PE': 73.11, 'ask4': 36.76, '跌停价': 32.35, '成交额': 3906.0, 'bid4_volume': 600, 'ask5_volume': 8500, 'bid5': 36.65, 'ipo_date_num': 0, 'sunhao_css': '', 'volume': 1073800.0, 'bid_volume': 574100, 'bid1': 36.72, 'low': 35.56, 'bid3': 36.7, '流通市值': 6.87, 'high': 37.02, '涨跌_css': 'font-red', 'ask1_volume': 1500, '涨跌': 0.8, '总市值': 27.38, 'turnover': 5.74, 'name': '至正股份', 'ask1_num': 5.51, 'ask2_volume': 1700, '振幅': 4.06, 'bid4': 36.66, '涨停价': 39.53, 'ask5': 36.77, 'cha': 0, '最近逐笔成交': '14:59:59/36.72/6/B/22030/32201|14:59:44/36.72/7/S/25710/32171|14:59:44/36.74/26/B/95517/32166|14:59:41/36.74/9/B/33066/32160|14:59:35/36.73/3/S/11019/32147|14:59:29/36.74/5/B/18370/32140', 'bid2': 36.71, 'ask2': 36.74, 'now': 36.74, 'ask3_volume': 100, 'open': 35.89}
#    leanDBAccess.saveTradeHistoryLeanCloud(t)
#    leanDBAccess.saveTradeHistoryLeanCloud(t,'S')
    
    return render_template('hello.html', position=auto_trader.getAllPositionFromSqlite())

@app.route('/info/')
def info():
    b = leanDBAccess.getBalanceLeanCloud()
    t = leanDBAccess.getTradeHistoryLeanCloud()
#    p = leanDBAccess.getPositionLeanCloud()
    return render_template('info.html', balance=b,tradehistory=t)
    
@app.route('/AllStockInfo/')
def getAllStockInfo():
    cloudfunc.rpc('getAllStockInfo')
    return 'OK'
    
@app.route('/position/')
def getPosition():
    cloudfunc.rpc('getPosition')
    return 'OK'

#@app.route('/buy/',methods=['POST'])
def buy():
    try:
        num = request.form['num']
        stockno = request.form['stockno']
        price = request.form['price']

        if len(stockno) != 6:
            return 'tockno error. stockno:' + stockno
        
        user = auto_trader.getUser()
        result=dict()
        
        result = user.buy(stockno, price, amount=num, entrust_prop='market')   
        
        print(result)
        return dictToString(result)
        
        #return "stock:" + stockno + ",num:" + num 
    except Exception as e:
        print(e)
        return e
    
def dictToString(sample_dic):
    result_str = []
    for key, value in sample_dic.items():
        result_str.append("'%s':'%s'" % (key, value))
    return ','.join(result_str)
    
#@app.route('/sell/',methods=['POST'])
def sell():
    try:
        num = request.form['num']
        stockno = request.form['stockno']
        price = request.form['price']

        if len(stockno) != 6:
            return 'tockno error. stockno:' + stockno

        user = auto_trader.getUser()
        result = user.sell(stockno, price, amount=num, entrust_prop='market')
        print(result)
        return dictToString(result)

    except Exception as e:
        print(e)
        return e

#批量取得最新行情 高频数据
@app.route('/qq/')
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

    #最小流通市值取得
    min_liutong = min(stockinfo.items(), key=lambda d:d[1]['流通市值'])[1]
#    print(min_liutong)
    #计算流通市值差
    for key,value in stockinfo.items():
        try:
            #市值差 （流通市值/最小流通市值）-1
            stockinfo[key]['cha'] = str(round((float(stockinfo[key]['流通市值'])/float(min_liutong['流通市值']) - 1)*100,2)) + '%'
            #去损耗市值差  （流通市值*现价/买1价）/（最小流通市值*现价/卖1价）-1
            liutong_sunhao = stockinfo[key]['流通市值']*stockinfo[key]['bid1']/stockinfo[key]['now']
            min_liutong_sunhao = min_liutong['流通市值']*min_liutong['ask1']/min_liutong['now']
            stockinfo[key]['cha_sunhao'] = str(round((liutong_sunhao/min_liutong_sunhao - 1)*100,2)) + '%'
            #上市天数计算
            d1 = datetime.datetime.strptime(dic[key], '%Y%m%d')
            ipo_date_num = (datetime.datetime.now()-d1).days
            stockinfo[key]['ipo_date_num'] = ipo_date_num if ipo_date_num > 50 else str(ipo_date_num) + ' 天'
            stockinfo[key]['ipo_date_num_css'] = 'font-red-bold' if ipo_date_num <= 50 else ''
            #该股为持仓股时，判断是否需要调仓
#            if key in dic_position.keys():
#                auto_trader.autoTrader(stockinfo[key],min_liutong,round((liutong_sunhao/min_liutong_sunhao - 1)*100,3))
        except:
            pass

    for key,value in stockinfo_zhangting.items():
        try:
            #上市天数计算
            d1 = datetime.datetime.strptime(dic[key], '%Y%m%d')
            ipo_date_num = (datetime.datetime.now()-d1).days
            stockinfo_zhangting[key]['ipo_date_num'] = ipo_date_num if ipo_date_num > 50 else str(ipo_date_num) + '天'
        except:
            pass

    return render_template('post_test.html', stockinfo_zhangting=stockinfo_zhangting,stockinfo_sort=temp)

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
        limit 50;
        '''
    #union all XXX 持仓股
        
    info_tid=sqlite3API.fetchmany(conn,sql_tid)
    dic = dict()
    stock_list=[]
    for info_temp in info_tid:
        dic[info_temp[0]] = str(info_temp[1])
        stock_list.append(info_temp[0])
    
    return dic,stock_list

if __name__ == '__main__':
    app.run(debug=True)


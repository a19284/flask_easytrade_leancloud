# -*- coding: utf-8 -*-

from leancloud import Object
from leancloud import Query

#持仓
def savePositionLeanCloud(p):
    Position = Object.extend('Position')
    position = Position()
    position.set('position',p)
    position.save()
    
#账户资金状况
def saveBalanceLeanCloud(b):
#    print('balance',b)
    if b:
        Balance = Object.extend('Balance')
        balance = Balance()
        balance.set('balance',b[0])
        balance.save()
    
#成交记录   
def saveTradeHistoryLeanCloud(t,flg='B'):
    TradeHistory = Object.extend('TradeHistory')
    tradeHistory = TradeHistory()
    tradeHistory.set('tradeHistory',t)
    tradeHistory.set('flg',flg)
    tradeHistory.save()

def getTradeHistoryLeanCloud():    
    TradeHistory = Object.extend('TradeHistory')
    tradeHistory = Query(TradeHistory)
#    tradeHistory.select('flg','tradeHistory')
    query_list = tradeHistory.find()
    result=[]
    for t in query_list:
        temp = []
        temp.append(t.get('flg'))
        temp.append(t.get('tradeHistory'))
        temp.append(t.get('createdAt'))
        result.append(temp)
#    print (query_list)
    return result

def getBalanceLeanCloud():    
    Balance = Object.extend('Balance')
    balance = Query(Balance)
    balance.select('balance')
    query_list = balance.find()
    result = []
    for q in query_list:
        dic = q.get('balance')
        dic['time'] = q.get('createdAt')
        result.append (dic)
    return result
    
def getPositionLeanCloud():    
    Position = Object.extend('Position')
    position = Query(Position)
    position.select('position')
    query_list = position.find()
#    print (str(query_list[0]))
    return query_list    
# -*- coding: utf-8 -*-

from leancloud import Object

#持仓
def savePositionLeanCloud(p):
    Position = Object.extend('Position')
    position = Position()
    position.set('position',p)
    position.save()
    
#账户资金状况
def saveBalanceLeanCloud(b):
    print('balance',b)
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

def getTradeHistryLeanCloud():    
    TradeHistory = Object.extend('TradeHistory')
    tradeHistory = TradeHistory.query
    tradeHistory.select('flg','tradeHistory')
    query_list = tradeHistory.find()
    print (query_list)
    return query_list

def getBalanceLeanCloud():    
    Balance = Object.extend('Balance')
    balance = Balance.query
    balance.select('balance')
    query_list = balance.find()
    print (query_list)
    return query_list    
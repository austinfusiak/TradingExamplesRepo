#!/usr/bin/python

import logging
import logger.logger as logger

class TradeActions():
	Void = -1  
	Buy = 0  
	Sell = 1 
	Match = 2 

	def __init__(self):
		pass

class Trade():

	def __init__(self):
		self.qty = 0 
		self.tradeAction = TradeActions.Void 
		self.buySellFactor = -1 
		self.symbol = None
		self.accountId = None 
		self.tradeId= None 
	
	def __init__(self, accountId, tradeId, qty, tradePrice, tradeAction, symbol, timestamp = None, extraInfo = {}, orderId = None ):
		self.accountId = accountId 
		self.tradeId = tradeId 
		self.qty = qty 
		self.tradePrice = tradePrice 
		self.tradeAction = tradeAction 
		self.buySellFactor = -1 if tradeAction == TradeActions.Sell else 1 
		self.symbol = symbol 
		self.orderId = orderId 
		self.timestamp = timestamp 
		self.extraInfo = extraInfo 
	
	def setSymbol(self, symbol):
		self.symbol = symbol 
	
	def getAccountId(self):
		return self.accountId 
	
	def getTradePrice(self):
		return self.tradePrice 
	
	def setAccountId(self, accountId):
		self.accountId = accountId 

	def setQty(self, qty):
		self.qty = qty 

	def setTradeAction(self, tradeAction):
		self.tradeAction = tradeAction 
		self.buySellFactor = -1 if tradeAction == TradeActions.Sell else 1 
	
	def setBuySell(self, buySellFactor):
		self.buySellFactor = buySellFactor 
	
	def __str__(self): 
		return str ( vars(self) )
	
	def __repr__(self): 
		return self.__str__() 

class TestTrade():

	@staticmethod
	def testTrade():
	
		l_aTrade = Trade( 1, 1, 100, 10.0, TradeActions.Buy, "AA" )
		l_aTrade.setAccountId(1)
		l_aTrade.setSymbol('AA')
		
		print l_aTrade
	

if __name__ == "__main__":
	
	logger.MyLogger.InitializeLogger()

	TestTrade.testTrade()


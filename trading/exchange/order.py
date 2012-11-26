#!/usr/bin/python

import logging
import logger.logger as logger

class OrderState():

	INITIAL_STATE = 0 
	ORDER_PENDING = 1 
	ORDER_PARTIAL_FILL = 2 
	ORDER_COMPLETE_FILL = 3 
	ORDER_FAILED_SUBMITED = 4 
	ORDER_CANCELED = 5 
	ORDER_FAILED = 6

	def __init__():
		pass

class OrderTypes():
	Void = 0 
	Market = 1 
	Limit = 2 

	def __init__(self):
		pass
 
class Order():
	def __init__(self, symbol, tradeAction, orderType, price, qty, acctId, orderId=None, extraInfo = {} ):
		self.symbol = symbol  
		self.tradeAction = tradeAction 
		self.orderType = orderType 
		self.price = price 
		self.qty = qty 
		self.originalQty = qty 
		self.orderId = orderId 
		self.acctId = acctId 
		self.state = None 
		self.extraInfo = extraInfo 
		
	def getSymbol (self):
		return self.symbol  

	def getTradeAction (self):
		return self.tradeAction 

	def getOrderType(self):
		return self.orderType 

	def getPrice(self):
		return self.price

	def getQty(self):
		return self.qty
	def setQty(self, qty):
		self.qty = qty
	
	def getOriginalQty(self):
		return self.originalQty 

	def getOrderId(self):
		return self.orderId
	def setOrderId(self, orderId):
		self.orderId = orderId

	def getAccountId(self):
		return self.acctId
	
	def __str__(self): 
		return str ( vars(self) )
	
	def __repr__(self): 
		return self.__str__() 

class TestOrder():

	@staticmethod
	def testOrder():
	
		import trade as trade

		l_aOrder = Order( "AA", trade.TradeActions.Buy, OrderTypes.Limit, 100, 0, 0, 1 ) 
		l_aOrder.getSymbol() 
		l_aOrder.getTradeAction() 
		l_aOrder.getOrderType()
		l_aOrder.getPrice()
		l_aOrder.getQty()
		l_aOrder.getOrderId()
		l_aOrder.getAccountId()
		
		print l_aOrder

if __name__ == "__main__":

	logger.MyLogger.InitializeLogger()

	TestOrder.testOrder()


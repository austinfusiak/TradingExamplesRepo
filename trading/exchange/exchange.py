#!/usr/bin/python

import order as order 
import trade as trade
import quote as quote 
import exchange_account as exchange_account
import exchange_participant as exchange_participant 
import order_book as order_book 
import logger.logger as logger
import logging

class Exchange( object ):

	"""
	This class provides the logic to match trades.  Specifically it can handle limit and market orders along with canceling 
	existing orders in the orderbook.  It keeps track of the currnet order book and diseminates trades via function calls 
	that can be registered by exchange participants.
	"""

	def __init__(self, symbol, transactionFeePercentage = 0):
		self.symbol = symbol 
		self.transactionFeePercentage = transactionFeePercentage 
		self.tradeId = 0  
		self.currentExchangeOrderId = 0 
		self.deleteOrderDict = {} # Price Level -> touple( bid or ask, price level, accountId ) used instead of search for deletion of orders from the book 
		self.funcOnQuoteListeners = {} # ExchangeAccount -> quoteFuncListener  
		self.funcOnTradeListeners = {} # ExchangeAccount -> tradeFuncListener  
		self.funcOnTradePriceListeners = {} # ExchangeAccount -> tradeFuncListener  
		self.orderBook = order_book.OrderBook(symbol) 
		self.logger = logging.getLogger('MyLogger')		
	
	def __str__ ( self ):
		returnStr = " ------------------- Printing Exchange Information for symbol:[%s] ------------------- \n" % ( self.symbol )  
		returnStr += self.orderBook.__str__() 
		return returnStr 
		
	def registerQuoteListener(self, exchangeAccount, funcOnQuote ):
		self.logger.info( "Registering quote listener for exchangeAccount:[%s]" % exchangeAccount )  
		self.funcOnQuoteListeners[ exchangeAccount.getAccountId() ] = funcOnQuote
	
	def registerTradeListener(self, exchangeAccount, funcOnTrade ):
		self.logger.info( "Registering trade listener for exchangeAccount:[%s]" % exchangeAccount )  
		self.funcOnTradeListeners[ exchangeAccount.getAccountId() ] = funcOnTrade 
		
	def registerTradePriceListener(self, exchangeAccount, funcOnTradePrice ): 
		self.logger.info( "Registering trade listener for exchangeAccount:[%s]" % exchangeAccount )  
		self.funcOnTradePriceListeners[ exchangeAccount.getAccountId() ] = funcOnTradePrice 
	
	def publishTrades(self, trades):
			
		for trade in trades: 
			self.logger.info( "PublishingTrade Trade:[%s]" % ( trade ) )  

			if trade == None: 
				continue 

			elif trade.getAccountId() in self.funcOnTradeListeners:
				publishFunc = self.funcOnTradeListeners[ trade.getAccountId() ] 
				publishFunc(trade) 
			else: 
				self.logger.warning( "Failed to publish trade to listener no listener attached accoutnId:[%s] tradeId:[%s]" % ( trade.getAccountId(), trade.tradeId ) ) 

	def validateOrder(self, currentOrder):
		# Validate symbol is correct for exchange, user is able to trade in that symbol, the qty is reasonable, the price is reasonable, etc.... 

		if currentOrder.getSymbol() != self.symbol: 
			self.logger.warning( "Failed to validate order, Invalid symbol for exchange order:[%s]" % ( currentOrder ) ) 
			raise Exception('Invalid Symbol for Exchange')

		if currentOrder.getQty() <= 0: 
			self.logger.warning( "Failed to validate order, Invalid Quantity order:[%s]" % ( currentOrder ) ) 
			raise Exception('Invalid Quantity, quantity most be a positive value')
			
		if currentOrder.getOrderType() == order.OrderTypes.Limit : # check price only for limit orders 
			if currentOrder.getPrice() <= 0:  # Although for some instruments negative prices are valid, we are not going to allow this here
				self.logger.warning( "Failed to validate order, Invalid Price order:[%s]" % ( currentOrder ) ) 
				raise Exception('Invalid Price, for limit orders price must be a positive value ')
	
	def createNewOrderId(self):
		self.currentExchangeOrderId += 1 
		return self.currentExchangeOrderId 
	
	def submitOrder(self, currentOrder):

		try:
			self.logger.info( "Processing submitOrder for order:[%s]" % ( currentOrder ) ) 
			
			self.validateOrder( currentOrder )
			currentOrder.setOrderId( self.createNewOrderId() )
			trades = []  
		
			if currentOrder.orderType == order.OrderTypes.Market: 
				if currentOrder.tradeAction == trade.TradeActions.Buy: 
					trades = trades + self.fillBuyOrder ( currentOrder ) 
				elif currentOrder.tradeAction == trade.TradeActions.Sell: 
					trades = trades + self.fillSellOrder ( currentOrder ) 
				else: 
					self.logger.warning( "Failed to handle Trade Action for order:[%s]" % ( currentOrder ) ) 
					raise Exception ("Failed to handle Trade Action")	

			elif currentOrder.orderType == order.OrderTypes.Limit: 
				if currentOrder.tradeAction == trade.TradeActions.Buy: 
					trades = trades + self.processLimitBuyOrder ( currentOrder )
				elif currentOrder.tradeAction == trade.TradeActions.Sell: 
					trades = trades + self.processLimitSellOrder ( currentOrder ) 
				else: 
					self.logger.warning( "Failed to handle Trade Action for order:[%s]" % ( currentOrder ) ) 
					raise Exception ("Failed to handle Trade Action")	
			
			else: 
				self.logger.warning( "Failed to handle Order Type for order:[%s]" % ( currentOrder ) ) 
				raise Exception ("Failed to handle Order Type")	
			
			if len(trades) > 0:
				self.publishTrades( trades ) 

			return ( True, currentOrder.getOrderId() ) 

		except Exception as ex:
			self.logger.exception( "Exception caught while processing orderId:[%s] exception:[%s]" % ( currentOrder.orderId, ex ) ) 
			return ( False, ex.args[0] )  

	def getSumerizedAllOpenOrdersForAccountId (self, accountId):
		# There should be validation that the current user can view the accountId orders
		# This method is not efficient for use here, current use case is only for testing purposes,
		# it should be modified to use a different data structure that is more efficient if using during application runtime 
		return list( (aOrderTuple) for orderId, aOrderTuple in self.deleteOrderDict.items() if aOrderTuple[2] == accountId )
	
	def cancelOrder(self, orderId):
		self.logger.info( "processing cancel order orderId:[%s]" % ( orderId ) )

		if orderId in self.deleteOrderDict: 
			tradeAction, priceLevel, accountId  = self.deleteOrderDict[ orderId ]
			self.orderBook.removeOrderFromOrderBook( tradeAction, priceLevel, orderId )
			del self.deleteOrderDict[orderId]
			return True

		else: 
			self.logger.warning ( "Failed to remove order from the order book. Could not find orderId:[%s]" % ( orderId ) )
			raise Exception ( "Failed to remove order from the order book.  Could not find orderId:[%s]. Order was likely already matched" % ( orderId ) ) 
	
	def matchTrade( self, currentOrder, matchOrder, matchPrice ):
				
		self.logger.info ( "Matching two orders currentOrderId:[%s], matchOrderId:[%s], matchPrice:[%f]" % ( currentOrder.orderId, matchOrder.orderId, matchPrice ) )
		self.logger.info ( "Matching two orders currentOrder:[%s]" % ( currentOrder ) )
		self.logger.info ( "Matching two orders matchOrder:[%s]" % ( matchOrder ) )

		trades = [] 
		self.tradeId += 1  
		tradeQty = min ( currentOrder.getQty(), matchOrder.getQty() )

		transactionFee = matchPrice * tradeQty * self.transactionFeePercentage 
		currentOrder.extraInfo ['transactionFee'] = transactionFee 
		matchOrder.extraInfo ['transactionFee'] = transactionFee 

		trades.append( trade.Trade ( currentOrder.getAccountId(), self.tradeId, tradeQty, matchPrice, currentOrder.getTradeAction(), self.symbol, extraInfo = currentOrder.extraInfo ) ) 
		trades.append( trade.Trade ( matchOrder.getAccountId(), self.tradeId, tradeQty, matchPrice, matchOrder.getTradeAction(), self.symbol, extraInfo = matchOrder.extraInfo ) ) 
			
		currentOrder.setQty( currentOrder.getQty() - tradeQty )
		matchOrder.setQty( matchOrder.getQty() - tradeQty )

		return trades 

	def processLimitBuyOrder ( self, currentOrder ): 
		if currentOrder.getPrice() >= self.orderBook.getLowestAskPrice()  and self.orderBook.getLowestAskPrice() is not None:  # Should fill limit order against market orders if possible 
			trades = self.fillBuyOrder( currentOrder, stoppingPrice = currentOrder.getPrice() )
			if currentOrder.getQty() > 0:
				self.orderBook.appendBuyOfferToOrderBook( currentOrder )
				self.deleteOrderDict [ currentOrder.getOrderId() ] = ( currentOrder.getTradeAction(), currentOrder.getPrice(), currentOrder.getAccountId() ) 
			return trades 
		else:  # Did not cross the market, only need to append to quote book
			self.orderBook.appendBuyOfferToOrderBook( currentOrder )
			self.deleteOrderDict [ currentOrder.getOrderId() ] = ( currentOrder.getTradeAction(), currentOrder.getPrice(), currentOrder.getAccountId() ) 
			return []

	def checkMatchBuyOrder ( self, matchOrder, processingData ) :

		currentOrder, trades, stoppingPrice  = processingData
		trades += self.matchTrade( currentOrder, matchOrder, matchOrder.getPrice() )
	
		if matchOrder.getQty() == 0:
			self.orderBook.removeSellOrderFromOrderBook ( matchOrder.getPrice(), matchOrder.getOrderId() )  
			del self.deleteOrderDict [ matchOrder.getOrderId() ]
	
		if stoppingPrice is not None : 
			if self.orderBook.getLowestAskPrice() > currentOrder.getPrice(): # Need to append new bid offer into the market 
				return False 
			
		if currentOrder.getQty() == 0:
			return False 
		
		return True 

	def fillBuyOrder( self, currentOrder, stoppingPrice = None):
		trades = [] 
		while currentOrder.getQty() > 0 :
			if self.orderBook.getLowestAskPrice() == None: 
				self.logger.warning ( "There are not enough orders in the ask book for completly fill the order" ) 
				return trades 
			
			processingData = ( currentOrder, trades, stoppingPrice ) 
			self.orderBook.visitAskOrders( self.checkMatchBuyOrder, processingData )
			
		return trades 

	def processLimitSellOrder ( self, currentOrder ): 
		if currentOrder.getPrice() <= self.orderBook.getHighestBidPrice() and self.orderBook.getHighestBidPrice() is not None:
			trades = self.fillSellOrder( currentOrder, stoppingPrice = currentOrder.getPrice() )
			if currentOrder.getQty() > 0:
				self.orderBook.appendSellOfferToOrderBook( currentOrder )
				self.deleteOrderDict [ currentOrder.getOrderId() ] = ( currentOrder.getTradeAction(), currentOrder.getPrice(), currentOrder.getAccountId() ) 
			return trades 
		else:
			self.orderBook.appendSellOfferToOrderBook( currentOrder )
			self.deleteOrderDict [ currentOrder.getOrderId() ] = ( currentOrder.getTradeAction(), currentOrder.getPrice(), currentOrder.getAccountId() ) 
			return []
	
	def checkMatchSellOrder ( self, matchOrder, processingData ) :

		currentOrder, trades, stoppingPrice  = processingData
		trades += self.matchTrade( currentOrder, matchOrder, matchOrder.getPrice() )
	
		if matchOrder.getQty() == 0:
			self.orderBook.removeBuyOrderFromOrderBook ( matchOrder.getPrice(), matchOrder.getOrderId() )  
			del self.deleteOrderDict [ matchOrder.getOrderId() ]
	
		if stoppingPrice is not None : 
			if self.orderBook.getHighestBidPrice() < currentOrder.getPrice(): # Need to append new bid offer into the market 
				return False 
			
		if currentOrder.getQty() == 0:
			return False 
			
		return True 

	def fillSellOrder( self, currentOrder, stoppingPrice = None):
		trades = [] 
		while currentOrder.getQty() > 0 :
				
			self.logger.info( "currentOrder.getQty():[%s], self.orderBook.getHighestBidPrice():[%s]" % ( currentOrder.getQty(), self.orderBook.getHighestBidPrice() ) ) 

			if self.orderBook.getHighestBidPrice() == None: 
				self.logger.warning ( "There are not enough orders in the ask book for completly fill the order" ) 
				return trades 
			
			processingData = ( currentOrder, trades, stoppingPrice ) 
			self.orderBook.visitBidOrders( self.checkMatchSellOrder, processingData )
			
		return trades 
	
	def clearExchange( self ): 
		self.orderBook.clearOrderBook() 
		self.deleteOrderDict = {} 
	
class TestExchange():
	
	@staticmethod
	def testExchangeCreateTestSetup():
		symbol = "AA"
		testExchange = Exchange( symbol )
		testExchangeParticipant1 = exchange_participant.ExchangeParticipant( exchange_account.ExchangeAccount(1) )
		testExchangeParticipant2 = exchange_participant.ExchangeParticipant( exchange_account.ExchangeAccount(2) )
		testExchange.registerTradeListener( testExchangeParticipant1.getAccount(), testExchangeParticipant1.onTrade )
		testExchange.registerTradeListener( testExchangeParticipant2.getAccount(), testExchangeParticipant2.onTrade )
		
		return ( symbol, testExchange, testExchangeParticipant1, testExchangeParticipant2 )  
		
	
	@staticmethod
	def testExchangeSubmitLimitOrderAgainstEmptyBook():
		
		( symbol, testExchange, testExchangeParticipant1, testExchangeParticipant2 )  = TestExchange.testExchangeCreateTestSetup()
		
		testOrder = order.Order( "AA", trade.TradeActions.Buy, order.OrderTypes.Limit, 10, 100, 0, testExchangeParticipant1.getAccount().getAccountId() ) 
		result = testExchange.submitOrder(testOrder)
		assert ( result[0] == True )  
		
		print "Test Completed Succesfully"	
	
	@staticmethod
	def testExchangeSubmitLimitOrderPartialFill():

		( symbol, testExchange, testExchangeParticipant1, testExchangeParticipant2 )  = TestExchange.testExchangeCreateTestSetup()
		
		# Setup test orders in the order book 
		testOrder = order.Order( "AA", trade.TradeActions.Buy, order.OrderTypes.Limit, 10, 100, 0, testExchangeParticipant1.getAccount().getAccountId() ) 
		result = testExchange.submitOrder(testOrder)
		assert ( result[0] == True )
		
		testOrder = order.Order( "AA", trade.TradeActions.Buy, order.OrderTypes.Limit, 9, 100, 0, testExchangeParticipant2.getAccount().getAccountId() ) 
		result = testExchange.submitOrder(testOrder)
		assert ( result[0] == True )
				
		testOrder = order.Order( "AA", trade.TradeActions.Sell, order.OrderTypes.Limit, 11, 100, 0, testExchangeParticipant2.getAccount().getAccountId() ) 
		result = testExchange.submitOrder(testOrder)
		assert ( result[0] == True )
		
		# Check full fill of limit order against book	
		testOrder = order.Order( "AA", trade.TradeActions.Sell, order.OrderTypes.Limit, 9, 175, 0, testExchangeParticipant2.getAccount().getAccountId() ) 
		result = testExchange.submitOrder(testOrder)
		assert ( result[0] == True )

		topOfBookQuote = testExchange.orderBook.getTopOfBook()
		testComparisonQuote = quote.Quote (symbol, 9, 11, 25, 100)
		assert ( topOfBookQuote == testComparisonQuote ) 
		
		# Check partial fill of limit order against book
		testOrder = order.Order( "AA", trade.TradeActions.Sell, order.OrderTypes.Limit, 9, 50, 0, testExchangeParticipant2.getAccount().getAccountId() ) 
		result = testExchange.submitOrder(testOrder)
		assert ( result[0] == True )  
		
		topOfBookQuote = testExchange.orderBook.getTopOfBook()
		testComparisonQuote = quote.Quote (symbol, None, 9, 0, 25)
		assert ( topOfBookQuote == testComparisonQuote ) 
		
		print "Test Completed Succesfully"	
		
	
	@staticmethod
	def testInvalidOrder():
		
		( symbol, testExchange, testExchangeParticipant1, testExchangeParticipant2 )  = TestExchange.testExchangeCreateTestSetup()

		testOrder = order.Order( symbol, trade.TradeActions.Buy, order.OrderTypes.Limit, -10 , 100, 0, testExchangeParticipant1.getAccount().getAccountId() ) 
		result = testExchange.submitOrder( testOrder )
		assert ( result[0] == False )  

		testOrder = order.Order( symbol, trade.TradeActions.Buy, order.OrderTypes.Limit, 10 , -10, 0, testExchangeParticipant1.getAccount().getAccountId() ) 
		result = testExchange.submitOrder( testOrder )
		assert ( result[0] == False )  
		
		testOrder = order.Order( "NOT SYMBOL", trade.TradeActions.Buy, order.OrderTypes.Limit, 10 , -10, 0, testExchangeParticipant1.getAccount().getAccountId() ) 
		result = testExchange.submitOrder( testOrder )
		assert ( result[0] == False )  
		
		print "Test Completed Succesfully"	


	@staticmethod
	def testExchangeCancelOrder():
		
		( symbol, testExchange, testExchangeParticipant1, testExchangeParticipant2 )  = TestExchange.testExchangeCreateTestSetup()
	
		testOrder = order.Order( symbol, trade.TradeActions.Buy, order.OrderTypes.Limit, 10, 100, 0, testExchangeParticipant1.getAccount().getAccountId() ) 
		result = testExchange.submitOrder( testOrder )
		assert ( result[0] == True )  

		topOfBookQuote = testExchange.orderBook.getTopOfBook()
		testComparisonQuote = quote.Quote (symbol, 10, None, 100, 0)
		assert ( topOfBookQuote == testComparisonQuote ) 
		
		testExchange.cancelOrder(1)

		topOfBookQuote = testExchange.orderBook.getTopOfBook()
		testComparisonQuote = quote.Quote (symbol, None, None, 0, 0)
		assert ( topOfBookQuote == testComparisonQuote ) 

		print "Test Completed Succesfully"	

if __name__ == "__main__":
	
	logger.MyLogger.InitializeLogger()
	
	TestExchange.testExchangeSubmitLimitOrderAgainstEmptyBook()
	TestExchange.testExchangeSubmitLimitOrderPartialFill()
	TestExchange.testInvalidOrder()
	TestExchange.testExchangeCancelOrder()


#!/usr/bin/python

import trading.exchange.order as order 
import trading.exchange.quote as quote 
import trading.exchange.trade as trade 
import logger.logger as logger 
import logging 

class CondencedOrderBook():

	"""
	This class represents a condenced order book.  The condensed order book does not contain information for specific orders 
	for each price level but rather provides the quanity of limit orders at each price.  This can more easily be used to view 
	the total quantity available at a price level and determine the average price you will obtain from a market order that 
	depletes mutliple price levels. 
	"""

	def __init__(self, symbol, bidOrderBook, askOrderBook, highestBidPrc = None, lowestAskPrc = None ):
		self.symbol = symbol 
		self.bidOrderBook = bidOrderBook # Price Level -> condenced order ( sum of all orders at that price level ) 
		self.askOrderBook = askOrderBook # Price Level -> condenced order ( sum of all orders at that price level ) 
		self.highestBidPrc = highestBidPrc 
		self.lowestAskPrc = lowestAskPrc 
		self.logger = logging.getLogger('MyLogger')		

	def getTotalAskQtyBelowPrice ( self, price ):
		return sum ( askQuote.asksz for priceLevel, askQuote in self.askOrderBook.iteritems() if priceLevel <= price ) 
	
	def getTotalBidQtyAbovePrice (self, price ):
		return sum ( bidQuote.bidsz for priceLevel, bidQuote in self.bidOrderBook.iteritems() if priceLevel >= price ) 
	
	def __str__ ( self ):
		returnStr = " ------------------- Printing Condenced Order Book for symbol:[%s] ------------------- \n" % ( self.symbol )  

		returnStr += " ----- BIDS ------ \n" 
		for price, condencedQuote in sorted( self.bidOrderBook.items() ):
				returnStr+= " price:[%s] bidPrice:[%s] bidSize:[%s]\n" % ( price, condencedQuote.bid, condencedQuote.bidsz  ) 
		
		returnStr += " ----- ASKS ------ \n" 
		for price, condencedQuote in sorted( self.askOrderBook.items() ):
				returnStr+= " price:[%s] askPrice:[%s] askSize:[%s]\n" % ( price, condencedQuote.ask, condencedQuote.asksz  ) 

		return returnStr 
		

class OrderBook():

	"""
	This class organizes all of the orders current submited to the market that have not be filled.  The order book contains 
	the orders via price lookup and organizes a queue of orders at an individual price levels to be filled.  It currently contains 
	the logic to add limit orders to both the bid and ask side of the market along with removing orders during market order fills or cancelations.
	"""

	def __init__(self, symbol):
		self.symbol = symbol 
		self.bidOrderBook = {} # Price Level -> dict[orderId] current bid orders for that price level
		self.askOrderBook = {} # Price Level -> dict[orderId] current ask orders for that price level
		self.highestBidPrc = None # Keeps track of the top of the book for bids
		self.lowestAskPrc = None # Keeps track of the top of the book for asks 
		self.logger = logging.getLogger('MyLogger')		

	def createCondencedOrderBook(self):
		
		self.logger.info('Creating Condenced Order Book') 
	
		condencedBidOrderBook = {}	
		for bidPrice, orderDict in sorted( self.bidOrderBook.items() ):
			bidsz = sum ( map (  lambda x: x.getQty(), self.bidOrderBook[ bidPrice ].values() ) )  
			q = quote.Quote ( self.symbol, bidPrice, None, bidsz, None )
			condencedBidOrderBook [ bidPrice ] = q 
		
		condencedAskOrderBook = {}	
		for askPrice, orderDict in sorted( self.askOrderBook.items() ):
			asksz = sum ( map (  lambda x: x.getQty(), self.askOrderBook[ askPrice ].values() ) )  
			q = quote.Quote (self.symbol, None, askPrice, None, asksz )
			condencedAskOrderBook [ askPrice ] = q 
		
		return CondencedOrderBook( self.symbol, condencedBidOrderBook, condencedAskOrderBook )
	
	def __str__ ( self ):

		returnStr = " ------------------- Printing Order Book for symbol:[%s] ------------------- \n" % ( self.symbol )  

		returnStr += " ----- BIDS ------ \n" 
		for price, orderDict in sorted( self.bidOrderBook.items() ):

			if not orderDict :
				returnStr+= " Empty Order Dict for price:[%s] \n" % ( price )

			for orderId, order in sorted( orderDict.items() ): 
				returnStr+= " price:[%s] orderId:[%s] tradeAction:[%s] orderQty:[%s] \n" % ( price, orderId, order.tradeAction, order.qty ) 
		
		returnStr += " ----- ASKS ------ \n" 
		for price, orderDict in sorted( self.askOrderBook.items() ):

			if not orderDict :
				returnStr+= " Empty Order Dict for price:[%s] \n" % ( price )

			for orderId, order in sorted( orderDict.items() ): 
				returnStr+= " price:[%s] orderId:[%s] tradeAction:[%s] orderQty:[%s] \n" % ( price, orderId, order.tradeAction, order.qty ) 

		return returnStr 
		
	def getTopOfBook( self ):
		bidsz = 0 
		asksz = 0 

		if self.highestBidPrc is not None :  
			bidsz = sum ( map (  lambda x: x.getQty(), self.bidOrderBook[ self.highestBidPrc ].values() ) )  
		
		if self.lowestAskPrc is not None :  
			asksz = sum ( map (  lambda x: x.getQty(), self.askOrderBook[ self.lowestAskPrc].values() ) )  

		return quote.Quote (self.symbol, self.highestBidPrc, self.lowestAskPrc, bidsz, asksz)
	
	def removeOrderFromOrderBook( self, tradeAction, priceLevel, orderId ):
		if tradeAction == trade.TradeActions.Buy: 
			self.removeBuyOrderFromOrderBook( priceLevel, orderId )
		elif tradeAction == trade.TradeActions.Sell: 
			self.removeSellOrderFromOrderBook( priceLevel, orderId )
	
	def removeBuyOrderFromOrderBook( self, priceLevel, orderId ):
		self.logger.info( "removing buy order priceLevel:[%s], orderId:[%s]" % ( priceLevel, orderId ) )

		del self.bidOrderBook[ priceLevel ][ orderId ] 
		if not self.bidOrderBook[ priceLevel ]: # Check for empty dict and delete empty dict 
			del self.bidOrderBook[ priceLevel ] # delete none existent price level 
			self.highestBidPrc = self.getNewHighestBidPrice()
			self.logger.info( "resetting highest bid price self.highestBidPrc:[%s]" % ( self.highestBidPrc ) ) 
	
	def removeSellOrderFromOrderBook( self, priceLevel, orderId ):
		self.logger.info( "removing sell order priceLevel:[%s], orderId:[%s]" % ( priceLevel, orderId ) )

		del self.askOrderBook[ priceLevel ][ orderId ] 
		if not self.askOrderBook[ priceLevel ]: # Check for empty dict and delete empty dict 
			del self.askOrderBook[ priceLevel ] # delete none existent price level 
			self.lowestAskPrc = self.getNewLowestAskPrice()
			self.logger.info( "resetting lowest ask price self.lowestAskPrc:[%s]" % ( self.lowestAskPrc ) ) 
	
	def appendOrderToOrderBook( self, currentOrder ):
		if currentOrder.getTradeAction() == trade.TradeActions.Buy: 
			self.appendBuyOfferToOrderBook( currentOrder )
		elif currentOrder.getTradeAction() == trade.TradeActions.Sell: 
			self.appendSellOfferToOrderBook( currentOrder )
	
	def appendBuyOfferToOrderBook( self, currentOrder ):
		if currentOrder.getPrice() not in self.bidOrderBook : # If price doesnt already exist in bidOrderBook
			self.bidOrderBook[ currentOrder.getPrice() ] = {} 

		self.bidOrderBook[ currentOrder.getPrice() ] [ currentOrder.getOrderId() ] = currentOrder 
	
		if self.highestBidPrc < currentOrder.getPrice() or self.highestBidPrc is None: # Updates Top price of the Quote Book
			self.highestBidPrc = currentOrder.getPrice()

		return
	
	def appendSellOfferToOrderBook( self, currentOrder ):
		if currentOrder.getPrice() not in self.askOrderBook : # If price doesnt already exist in bidOrderBook
			self.askOrderBook[ currentOrder.getPrice() ] = {} 

		self.askOrderBook[ currentOrder.getPrice() ] [ currentOrder.getOrderId() ] = currentOrder 
		
		if self.lowestAskPrc > currentOrder.getPrice() or self.lowestAskPrc is None: # Updates Top price of the Quote Book
			self.lowestAskPrc = currentOrder.getPrice()
		
		return

	def visitBidOrders(self, funcToProcess, data ):
		for orderId, bidOrderInBook in sorted( self.bidOrderBook[ self.highestBidPrc ].iteritems() ): # Sorted by OrderID for price book position 
			self.logger.info( 'visiting order book bid order for bidOrderInBook:[%s]' % ( bidOrderInBook ) )
			continueIteration = funcToProcess ( bidOrderInBook, data )
			if continueIteration == False:
				self.logger.info( 'Iteration through bid order book not continueing' ) 
				return 
				
		self.logger.info( 'Finished visiting bid offers' ) 
		return
	
	def visitAskOrders(self, funcToProcess, data ):
		for orderId, askOrderInBook in sorted( self.askOrderBook[self.lowestAskPrc].iteritems() ): # Sorted by OrderID for price book position 
			self.logger.info( 'visiting order book ask order for askOrderInBook:[%s]' % ( askOrderInBook ) )
			continueIteration = funcToProcess ( askOrderInBook, data )
			if continueIteration == False:
				self.logger.info( 'Iteration through ask order book not continueing' ) 
				return 
		
		self.logger.info( 'Finished visiting ask offers' ) 
		return

	def getLowestAskPrice(self):
		return self.lowestAskPrc 
	
	def getHighestBidPrice(self):
		return self.highestBidPrc
	
	def getNewLowestAskPrice(self):
		if len ( self.askOrderBook ) == 0: 
			return None 
		else :
			return min ( self.askOrderBook.keys(), key=float )
	
	def getNewHighestBidPrice(self):
		if len ( self.bidOrderBook ) == 0: 
			return None 
		else :
			return max ( self.bidOrderBook.keys(), key=float )
	
	def clearOrderBook ( self ): 
		self.bidOrderBook = {} 
		self.askOrderBook = {} 
	
class TestOrderBook():
	
	@staticmethod
	def createTestOrderBook( symbol, bidMinPrice, bidMaxPrice, askMinPrice, askMaxPrice, qty, ordersAtBidPriceLevel = 1, ordersAtAskPriceLeve = 1 ):
		accountId = 1 
		orderId = 1 
		testOrderBook = OrderBook(symbol)
		
		for samplePrice in range ( askMinPrice, askMaxPrice + 1 ): 
			for i in range (0, ordersAtAskPriceLeve) : 
				testOrder = order.Order( symbol, trade.TradeActions.Sell, order.OrderTypes.Limit, samplePrice, qty, accountId, orderId ) 
				testOrderBook.appendOrderToOrderBook( testOrder )
				orderId += 1 
		
		for samplePrice in range ( bidMinPrice, bidMaxPrice + 1 ): 
			for i in range (0,ordersAtBidPriceLevel): 
				testOrder = order.Order( symbol, trade.TradeActions.Buy, order.OrderTypes.Limit, samplePrice, qty, accountId, orderId ) 
				testOrderBook.appendOrderToOrderBook( testOrder )
				orderId += 1 
		
		return testOrderBook 
	
	@staticmethod
	def testOrderBook(): 
		symbol = "AA"
		testOrderBook = TestOrderBook.createTestOrderBook( symbol, 97, 99, 101, 103, 10, 2, 2) 
		assert ( testOrderBook.getLowestAskPrice() == 101 ) 
		assert ( testOrderBook.getHighestBidPrice() == 99 ) 
	
	@staticmethod
	def testCondencedOrderBook(): 
		symbol = "AA"
		testOrderBook = TestOrderBook.createTestOrderBook( symbol, 97, 99, 101, 103, 10, 2, 2) 
		condencedOrderBook = testOrderBook.createCondencedOrderBook()
		
		topOfBookQuote = testOrderBook.getTopOfBook()
		testComparisonQuote = quote.Quote (symbol, 99, 101, 20, 20 ) 
		assert ( topOfBookQuote == testComparisonQuote ) 

		assert ( condencedOrderBook.getTotalAskQtyBelowPrice ( 110 ) == 60 ) 
		assert ( condencedOrderBook.getTotalBidQtyAbovePrice ( 90 ) == 60 ) 

if __name__ == "__main__":
	
	logger.MyLogger.InitializeLogger()
	TestOrderBook.testOrderBook()
	TestOrderBook.testCondencedOrderBook()
	

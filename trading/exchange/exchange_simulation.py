#!/usr/bin/python

import trading.time_series.time_series as time_series 
import trading.exchange.order as order
import trading.exchange.quote as quote 
import trading.exchange.trade as trade 
import trading.exchange.exchange as exchange 
import trading.exchange.exchange_participant as exchange_participant 
import trading.exchange.exchange_account as exchange_account
import logger.logger as logger 
import logging

class ExchangeSimulation ( exchange.Exchange ):

	"""
	This class which inherites from the exchange class provides an interface to process historical trade data.  Upon 
	recieving a historical price it assumes that all of the current limit orders are fill according to buy/sell and 
	the current price.  This class does not make any assumptions of the trade quantity and assumes all market orders 
	below/above ( buy/sell ) the price are filled.
	"""

	def __init__(self, symbol, transactionFeePercentage = 0 ):
		super(ExchangeSimulation, self).__init__( symbol, transactionFeePercentage )

		# Need a test participant during simulation for creating initial top of market
		self.exchangeParticipant = exchange_participant.ExchangeParticipant( exchange_account.ExchangeAccount(0) )
		self.lastTradePoint = None 
		self.topOfBookOrders = {}	
	
		# Only handles fills for top of book orders	
		self.registerTradeListener( self.exchangeParticipant.getAccount(), self.onTradeUpdate )

	def onTradeUpdate(self, exchangeTrade ):
		# Does not handle partial fills, there is no need to due to the logic below to fill orders completly
		if exchangeTrade.orderId is not None: 
			if exchangeTrade.orderId in self.topOfBookOrders: 
				del self.topOfBookOrders[ exchangeTrade.orderId ] 
	
	def initTopOfBookWithPrice (self, price, spread = .01):

		self.logger.info ("Creating Top Of Book Quotes during initialization, price:[%s], spread:[%s]" % ( price, spread ) )

		# Remove previous top of book orders if they are there
		for orderId in self.topOfBookOrders.keys():
			self.logger.info ("reinitializing top of book for simulation, canceling orderId:[%s]" % orderId ) 
			try : 
				self.cancelOrder(orderId, surpressLogging = True )
			except :
				self.logger.info( "Failed to cancel orderId:[%s]" % ( orderId ) )
		
		# Delete all entries  
		self.topOfBookOrders = {}	
		
		topOfBookQuote = self.orderBook.getTopOfBook()
		self.logger.info ("Top Of Book after deleting initialization orders topOfBookQuote:[%s]" % ( topOfBookQuote  ) ) 
		
		testOrder = order.Order( self.symbol, trade.TradeActions.Buy, order.OrderTypes.Limit, (price - spread), 1, 0, self.exchangeParticipant.getAccount().getAccountId() ) 
		result = super(ExchangeSimulation, self).submitOrder(testOrder)
		if result[0] != True :
			raise Exception("Failed to submit trade to initialize order book")

		self.topOfBookOrders[ result[1] ] = testOrder 
		
		testOrder = order.Order( self.symbol, trade.TradeActions.Sell, order.OrderTypes.Limit, (price + spread), 1, 0, self.exchangeParticipant.getAccount().getAccountId() ) 
		result = super(ExchangeSimulation, self).submitOrder(testOrder)
		if result[0] != True :
			raise Exception("Failed to submit trade to initialize order book")
		
		self.topOfBookOrders[ result[1] ] = testOrder 
		
		self.lastTradePoint = price 
	
	def runHistoricalTradeAsMarketOrder(self, tradeDataPoint):
		self.logger.info ("Running time series data processing data point:[%s]" % ( tradeDataPoint ) ) 
		#self.logger.debug ("Running time series data processing current order book:[%s]" % ( self.orderBook ) ) 

		trades = []
		if tradeDataPoint > self.lastTradePoint: # Assume all ask orders below that ammount have been filled
			for priceLevel, aOrderIdDict in sorted( self.orderBook.askOrderBook.items() ): 
				if priceLevel >= tradeDataPoint:
					break
				for aOrderId, aOrder in aOrderIdDict.items(): 
					self.logger.info ("Matching order price increased aOrder:[%s]" % ( aOrder ) ) 
					self.tradeId += 1 
					eInfo = aOrder.extraInfo 
					eInfo ['transactionFee'] = aOrder.getPrice() * aOrder.getQty() * self.transactionFeePercentage 
					trades.append( trade.Trade( aOrder.getAccountId(), self.tradeId, aOrder.getQty(), aOrder.getPrice(), aOrder.getTradeAction(), self.symbol, extraInfo = eInfo ))
					self.orderBook.removeSellOrderFromOrderBook ( aOrder.getPrice(), aOrder.getOrderId() ) 
					del self.deleteOrderDict [ aOrder.getOrderId() ]
		
		elif tradeDataPoint < self.lastTradePoint: # Assume all bid orders below that ammount have been filled 
			for priceLevel, aOrderIdDict in sorted (self.orderBook.bidOrderBook.items(), reverse = True ): 
				if priceLevel <= tradeDataPoint:
					break
				for aOrderId, aOrder in aOrderIdDict.items():  
					self.logger.info ("Matching order price decreased aOrder:[%s]" % ( aOrder ) ) 
					self.tradeId += 1  
					eInfo = aOrder.extraInfo 
					eInfo ['transactionFee'] = aOrder.getPrice() * aOrder.getQty() * self.transactionFeePercentage 
					trades.append( trade.Trade( aOrder.getAccountId(), self.tradeId, aOrder.getQty(), aOrder.getPrice(), aOrder.getTradeAction(), self.symbol, extraInfo = eInfo ))
					self.orderBook.removeBuyOrderFromOrderBook ( aOrder.getPrice(), aOrder.getOrderId() ) 
					del self.deleteOrderDict [ aOrder.getOrderId() ]

		if len (trades) > 0:
			self.publishTrades(trades)

		for accountId, funcOnTradePrice in self.funcOnTradePriceListeners.items(): 
			funcOnTradePrice(tradeDataPoint) 
			
		self.lastTradePoint = tradeDataPoint 
	
	def runTimeSeriesAsMarketOrderTrades (self, aTimeSeries ):
		
		self.logger.info ("Running time series data as trades aTimeSerise:[%s]" % ( aTimeSeries ) ) 
			
		for tradeDataPoint in aTimeSeries:
			self.runHistoricalTradeAsMarketOrder( tradeDataPoint )
		
	
class TestExchangeSimulation():
	
	@staticmethod
	def testCreateQuoteList(): 
		quoteTimeList = [ ] # Prepare quotes to send to client for controlled testing
		quoteTimeList.append ( quote.Quote( symbol, 12.00, 12.01, 1, 1 ) ) 
		quoteTimeList.append ( quote.Quote( symbol, 12.00, 12.05, 1, 1 ) ) 
		return quoteTimeList 
	
	@staticmethod
	def testCreateTradeList(): 
		tradeTimeSeries = time_series.TimeSeries( [11,10,11] ) 
		return tradeTimeSeries 

	@staticmethod
	def testWithPredeterminedTimeSeries(): 

		# Initial Setup
		symbol = "TEST_SYMBOL" 
		
		tradeTimeSeries = TestExchangeSimulation.testCreateTradeList()

		# This can be merged with the trade data to replicate changes in the order book from the exchange if data is available
		#quoteTimeSeries = TestExchangeSimulation.testCreateQuoteList()  

		testExchangeSimulation = ExchangeSimulation( symbol )
		
		# Test Initial Setting of the top of the book	
		timeSeriesArray = tradeTimeSeries.getTimeSeries() 
		initPrice = timeSeriesArray.pop() 
		testExchangeSimulation.initTopOfBookWithPrice ( initPrice ) 
		topOfBookQuote = testExchangeSimulation.orderBook.getTopOfBook()
		testComparisonQuote = quote.Quote (symbol, (initPrice - .01), (initPrice + .01), 1, 1)
		assert ( topOfBookQuote == testComparisonQuote ) 

		# Test Simulation
		testExchangeSimulation.runTimeSeriesAsMarketOrderTrades( timeSeriesArray ) 
		
if __name__ == "__main__":
	
	logger.MyLogger.InitializeLogger()
	
	TestExchangeSimulation.testWithPredeterminedTimeSeries()


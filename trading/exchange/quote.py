#!/usr/bin/python

import logging
import logger.logger as logger

class Quote():
	def __init__(self, symbol, bid, ask, bidsz, asksz):
		self.symbol = symbol
		self.bid = bid
		self.ask = ask
		self.bidsz = bidsz
		self.asksz = asksz

	def __eq__(self, other):
		if self.symbol != other.symbol or \
		   self.bid != other.bid or \
		   self.ask != other.ask or \
		   self.bidsz != other.bidsz or \
		   self.asksz != other.asksz:
			return False
		else: 
			return True 

	def __str__(self): 
		return str ( vars(self) )

class TestQuote():

	@staticmethod 
	def testQuoteComparison():
		testQuote = Quote ( "AA", 100, 101, 10, 12 )  
		testQuote2 = Quote ( "AA", 100, 101, 10, 12 )  
		testQuote3 = Quote ( "AA", 101, 101, 10, 12 )  

		assert ( testQuote == testQuote2 ) 
		assert ( testQuote != testQuote3 ) 

if __name__ == "__main__":

	TestQuote.testQuoteComparison()

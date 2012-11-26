#!/usr/bin/python

import exchange_account as exchange_account
import trade as trade 

class ExchangeParticipant( object ):

	def __init__(self, exchangeAccount ):
		self.exchangeAccount = exchangeAccount 
	
	def getAccount(self):
		return self.exchangeAccount 

	def onTrade (self, trade): 
		print "onTrade :: Trade Occured exchangeAccount:[%s] trade:[%s]" % ( self.exchangeAccount, trade ) 
	
	def __str__(self): 
		return str ( vars(self) )

class TestExchangeParticipant( object ):

	@staticmethod
	def testExchangeParticipant():
		l_aExchangeParticipant1 = ExchangeParticipant( exchange_account.ExchangeAccount(1) )
		print l_aExchangeParticipant1 

if __name__ == "__main__":

	TestExchangeParticipant.testExchangeParticipant()


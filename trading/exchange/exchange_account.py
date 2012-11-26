#!/usr/bin/python

class ExchangeAccount():
	def __init__(self, accountId):
		self.accountId = accountId

	def getAccountId(self): 
		return self.accountId 
	
	def __str__(self): 
		return str ( vars(self) )

class TestExchangeAccount():

	@staticmethod
	def testExchangeAccount():
		l_aExchangeAccount = ExchangeAccount(1)
		print l_aExchangeAccount 
		assert ( l_aExchangeAccount.getAccountId() == 1 )  
		

if __name__ == "__main__":

	TestExchangeAccount.testExchangeAccount()


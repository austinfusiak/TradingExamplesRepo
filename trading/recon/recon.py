#!/usr/bin/python

class Reconsiliation():

	"""
	This class provides a method to do a reconsilation between two dictionaries and find the corresponding differences between the values.
	"""

	@staticmethod	
	def runRecon( containerA, containerB, equalityFunc ):

		reconReport = {} 

		for keyA, valueA in containerA.items():
			if keyA in containerB: 
				valueB = containerB[ keyA ] 
				if not equalityFunc ( valueA, valueB ): 
					reconReport[keyA] = ( valueA, valueB )   
				del containerB[ keyA ] 
			else: 
				reconReport[keyA] = ( valueA, None )   
		
		for keyB, valueB in containerB.items():
			reconReport[keyB] = ( None, valueB )   
		
		return reconReport 

class TestReconsiliation():

	@staticmethod	
	def testWithStaticData():	
	
		containerA = {}
		containerA['a'] = 5 

		containerB = {}
		containerB['a'] = 5 

		def equalityFunc( valueA, valueB ) :
			return ( valueA == valueB )  
		
		reconReport = Reconsiliation.runRecon( containerA, containerB, equalityFunc )
		assert ( len(reconReport) == 0 )  
		
		containerATest2 = {}
		containerATest2['a'] = 5 

		containerBTest2 = {}
		containerBTest2['a'] = 5 
		containerBTest2['b'] = 1 
		
		reconReport = Reconsiliation.runRecon( containerATest2, containerBTest2, equalityFunc )
		assert ( len(reconReport) == 1 )  

if __name__ == "__main__":
	
	TestReconsiliation.testWithStaticData()


#!/usr/bin/python

import logging
import datetime
import sys 
import os  

class MyLogger():

	@staticmethod
	def InitializeLogger():

		LOGGING_FILE_NAME = '/Users/austinfusiak/repo/current/data/logging/example.' + datetime.datetime.utcnow().strftime('%Y-%m-%d_%H:%M:%S') + '.log'
		LOGGING_FORMAT = '%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
		logger = logging.getLogger('MyLogger')

		# remove any existing loggers
		for h in logger.handlers:
    			logger.removeHandler(h)

		# Set logging level and create formatter for handlers below
		logger.setLevel( logging.INFO )
		formatter = logging.Formatter(LOGGING_FORMAT) 
		
		# Logging to stdout
        	hdlr = logging.StreamHandler( sys.stdout )
        	hdlr.setFormatter( formatter )
        	logger.addHandler(hdlr)

		# Logging to file 
		#hdlr2 = logging.FileHandler( LOGGING_FILE_NAME )
		#hdlr2.setFormatter(formatter)
		#logger.addHandler(hdlr2)
	
		logger.propagate = False 

		logging.info('Created Logger MyLogger') 

class TestMyLogger():

	@staticmethod
	def testMyLogger():	
		logger.MyLogger.InitializeLogger()
		myLog = logging.getLogger('MyLogger')	
		myLog.info('Testing My Logger') 

if __name__ == "__main__":

	TestMyLogger.testMyLogger()


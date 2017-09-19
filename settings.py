import ConfigParser, os
from utils import *

class Settings(object):

	c = ConfigParser.ConfigParser()

	def __init__(self, pair):
		self._path = "./config/%s.ini" % pair
		self.settings = self.parseConfig

		
		printInfo("Checking config file .....\n")
		if not os.path.isfile(self._path):
			printInfo("No config file ..... will create one")
			self.createConfig()

		self.settings = self.parseConfig()

		if not self.validateConfig():
			quit()

	def parseConfig(self):
		settings = {}
		self.c.read(self._path)
		
		for o in self.c.options("Settings"):
			try:
				settings[o] = float(self.c.get("Settings", o))
			except:
				settings[o] = self.c.get("Settings", o)

		return settings


		
	def createConfig(self):
		with open(self._path, 'w') as f:
			self.c.add_section('Settings')
			self.c.set('Settings', 'candlestickPeriod', 1800)
			self.c.set('Settings', 'candlestickHours', 6)
			self.c.set('Settings', 'ema', 4)
			self.c.set('Settings', 'maxBalance', 0.85)
			self.c.set('Settings', 'profitMargin', 1.01)
			self.c.set('Settings', 'longMargin', 0.985)
			self.c.set('Settings', 'shortMargin', 1.02)
			self.c.set('Settings', 'delta', 0.9)
			self.c.set('Settings', 'stopLimit', 0.05)
			self.c.set('Settings', 'stopLimitTimeout', 2.5)
			self.c.set('Settings', 'marginCloseTimeout', 2)
			self.c.write(f)

		printSuccess("Config file generated, please modify the config file and re-run this script")
		quit()



	def validateConfig(self):
		ok = True

		if self.settings["longmargin"] >= 1.0:
			printError("Long margin cannot be >= 1.00")
			ok = False
	
		if self.settings["shortmargin"] <= 1.0:
			printError("Short margin cannot be <= 1.00")
			ok = False
	
		if self.settings["profitmargin"] <= 1.0:
			printError("Profit margin cannot be <= 1.0")
			ok = False

		if self.settings["candlestickperiod"] not in [300, 900, 1800, 7200, 14400, 86400]:
			printError("Invalid candle stick period, use 300, 900, 1800, 7200, 14400, or 86400")
			ok = False

		if self.settings["maxbalance"] <= 0.0:
			printError("Max balance cannot be < 0.0")
			ok = False

		if self.settings["maxbalance"] >= 0.95:
			printError("Max balance cannot be >= 0.95")
			ok = False

		if self.settings["stoplimit"] <= 0.01:
			printError("Stop limit cannot be <= 0.01")
			ok = False

		if self.settings["stoplimittimeout"] < 0.5:
			printError("Stop limit timeout cannot be less than 0.5 hours")
			ok = False

		if self.settings["marginclosetimeout"] < 1:
			printError("Margin close timeout cannot be < 1")
			ok = False

		return ok



	def refresh(self):
		oldSettings = self.settings
		self.settings = self.parseConfig()

		if not self.validateConfig():
			self.settings = oldSettings
			quit()

		print "\n"
		for key in self.settings:
			if self.settings[key] != oldSettings[key]:
				printHeader(">> %s changed from %s to %s" % (key, oldSettings[key], self.settings[key]))

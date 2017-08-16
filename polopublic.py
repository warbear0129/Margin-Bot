import poloniex, datetime, time
from utils import *

class PoloPublic(object):
	"""
	The PoloPublic object is used to retrieve data from
	Poloniex Public API which does not require API Keys
	such as chart data, ticker data
	"""

	def __init__(self, pair, config):
		self._client = poloniex.Poloniex()
		self._pair = pair
		self._hours_candlestick = config["candlestickhours"]
		self._period_candlestick = config["candlestickperiod"]
		self._data_chart = None
		self._data_ticker = None


	@property
	def data_chart(self):
		return self._data_chart
	
		
	@property
	def data_ticker(self):
		return self._data_ticker


	def refresh(self, settings):
		self._hours_candlestick = settings["candlestickhours"]
		self._period_candlestick = settings["candlestickperiod"]

		printInfo("Getting chart data .....")
		datetime_end = datetime.datetime.now()
		unix_end = time.mktime(datetime_end.timetuple())
		unix_start = time.mktime((datetime_end - datetime.timedelta(hours=self._hours_candlestick)).timetuple())

		self._data_chart = do(
			self._client.returnChartData,
			self._pair,
			self._period_candlestick,
			unix_start,
			unix_end
		)

		printInfo("Getting ticker data .....")
		self._data_ticker = do(self._client.returnTicker)[self._pair]




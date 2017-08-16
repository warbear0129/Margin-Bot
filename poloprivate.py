import os, poloniex, time, datetime
from utils import *

class PoloPrivate(object):
	"""
	The PoloPrivate object is used to control one's account's
	private API information such as margin position and to 
	perform actions such as placing and cancelling of orders
	"""

	def __init__(self, pair, config):
		self._balance_max = config["maxbalance"]
		self._profit_margin = config["profitmargin"]
		self._stop_limit = config["stoplimit"]
		self._long_margin = config["longmargin"]
		self._short_margin = config["shortmargin"]
		self._maximum_delta = config["delta"]
		self._stop_limit_timeout = config["stoplimittimeout"]

		self._pair = pair
		self._margin_position = None

		self._opening_order = {}
		self._opening_time = "Never"
		self._last_opening_dict = {}
		
		self._closing_order = {}
		self._closing_time = "Never"
		self._last_closing_dict = {}
		
		self._status = "none"
		self._turnovers = []

		printInfo("Checking API key and secret .....")
		self._client = self._check_API()

		printInfo("\nChecking open orders for %s ....." % self._pair)
		self._open_orders = do(
			self._client.returnOpenOrders,
			self._pair
		)
		self._cancel_open_orders()

		printInfo("\nChecking margin account balance .....")
		self._balance = self._check_balance()


	@property
	def status(self):
		return self._status


	@property
	def closing_time(self):
		return self._closing_time


	@property
	def opening_time(self):
		return self._opening_time


	@property
	def last_opening_dict(self):
		return self._last_opening_dict


	@property
	def last_closing_dict(self):
		return self._last_closing_dict


	@property
	def margin_position(self):
		return self._margin_position


	def refresh(self, config):
		self._balance_max = config["maxbalance"]
		self._stop_limit = config["stoplimit"]
		self._long_margin = config["longmargin"]
		self._short_margin = config["shortmargin"]
		self._profit_margin = config["profitmargin"]
		self._maximum_delta = config["delta"]
		self._stop_limit_timeout = config["stoplimittimeout"]

		printInfo("Getting margin position .....")
		self._margin_position = do(
			self._client.getMarginPosition,
			self._pair
		)

		if self._status != str(self._margin_position["type"]):
			# On margin position close
			if self.status != "none":
				self._cancel_open_orders()
				printSuccess("Margin position closed, will wait 5 minutes")
				time.sleep(300)
				self._balance = self._check_balance()
				self._turnovers.append(self.status)
				self._closing_time = datetime.datetime.utcnow().strftime("%d/%m/%Y  %H:%M")

			# On margin position open
			else:
				self._opening_time = datetime.datetime.utcnow().strftime("%d/%m/%Y  %H:%M")		

		printInfo("Getting open orders .....")
		self._open_orders = do(
			self._client.returnOpenOrders,
			self._pair
		)

		self._status = str(self._margin_position["type"])
		self._opening_order = self._get_order(self._opening_order)
		self._closing_order = self._get_order(self._closing_order)



	def open(self, ema, lowest_ask, highest_bid):
		result = ""
		dict_opening_order = self._create_opening_order(ema, lowest_ask, highest_bid)

		if self._opening_order == {} and dict_opening_order["delta"] <= self._maximum_delta:
			if dict_opening_order["type"] != self._last_opening_dict["type"]:
				self._cancel_open_orders()

			try:
				self._opening_order = dict_opening_order["func"](
					self._pair,
					dict_opening_order["rate"],
					dict_opening_order["amount"],
					0.02
				)
				result = "Created %s order at %s" % (dict_opening_order["type"], formatFloat(dict_opening_order["rate"]))

			except Exception, e:
				result = "Error creating order: %s" % e.message

		elif dict_opening_order["delta"] > self._maximum_delta:
			self._cancel_open_orders()
			result = "Delta is too high ....."

		elif self._last_opening_dict["rate"] != dict_opening_order["rate"]:
			self._opening_order["orderNumber"] = self._move_order(
				self._opening_order["orderNumber"],
				dict_opening_order["rate"],
				dict_opening_order["amount"],
			)

			result = "Moved opening order to %s" % (formatFloat(dict_opening_order["rate"]))

		else:
			result = "Waiting for %s position to open" % dict_opening_order["type"]

		self._last_opening_dict = dict_opening_order

		return result

	
	def update_open(self, ema, lowest_ask, highest_bid):
		result = ""
		dict_opening_order = self._create_opening_order(ema, lowest_ask, highest_bid)

		if self._opening_order != {}:
			if dict_opening_order["delta"] > self._maximum_delta or dict_opening_order["type"] != self._last_opening_dict["type"]:

				dict_cancel_type = {"LONG": "buy", "SHORT": "sell"}
				orders_to_cancel = self._filter_orders("type", dict_cancel_type[self._last_opening_dict["type"]])

				while orders_to_cancel != []:

					for order in orders_to_cancel:

						printError("Cancelling order %s" % order["orderNumber"])

						try:
							self._client.cancelOrder(order["orderNumber"])

						except Exception, e:
							printError("Error cancelling order: %s" % e.message)

					orders_to_cancel = self._filter_orders("type", dict_cancel_type[self._last_opening_dict["type"]])

				result = ", cancelling opening orders - delta too high / opening type changed"
			
			elif self._last_opening_dict["rate"] != dict_opening_order["rate"]:
				self._opening_order["orderNumber"] = self._move_order(
					self._opening_order["orderNumber"],
					dict_opening_order["rate"],
					dict_opening_order["amount"],
				)

				result = ", moved opening order to %s" % (formatFloat(dict_opening_order["rate"]))

		else:
			if dict_opening_order["total"] <= 0.0001:
				pass

			elif dict_opening_order["delta"] <= self._maximum_delta:
				try:
					self._opening_order = dict_opening_order["func"](
						self._pair,
						dict_opening_order["rate"],
						dict_opening_order["amount"],
						0.02
					)
					result = ", created %s order at %s" % (dict_opening_order["type"], formatFloat(dict_opening_order["rate"]))

				except Exception, e:
					result = ", error creating order: %s" % e.message
		
		self._last_opening_dict = dict_opening_order

		return result

				

	def close(self):
		result = ""
		dict_closing_order = self._create_closing_order()

		if float(self._margin_position["pl"]) <= -(self._balance * self._stop_limit):
			result = self._force_close("Stop limit triggered")
			printError("Stop limit triggered, will wait %s hours" % self._stop_limit_timeout)
			time.sleep(self._stop_limit_timeout * 3600)

		elif dict_closing_order["rate"] < 0 or float(self._margin_position["basePrice"]) < 0:
			result = self._force_close("Invalid rate")

		elif self._closing_order == {}:
			try:
				self._closing_order = dict_closing_order["func"](
					self._pair,
					dict_closing_order["rate"],
					dict_closing_order["amount"],
					0.02
				)	
				result = "Created closing order at %s" % formatFloat(dict_closing_order["rate"])

			except Exception, e:
				if str(e.message) == "Total must be at least 0.0001.":
					result = self._force_close("Invalid total")

				else:
					result = "Error creating closing order: %s" % e.message

	
		elif self._last_closing_dict["amount"] != dict_closing_order["amount"] or self._last_closing_dict["rate"] != dict_closing_order["rate"]:
			self._closing_order["orderNumber"] = self._move_order(
				self._closing_order["orderNumber"],
				dict_closing_order["rate"], 
				dict_closing_order["amount"]
			)

			result = "Moved closing order to %s" % formatFloat(dict_closing_order["rate"])

		else:
			result = "Waiting for margin position to close"

		self._last_closing_dict = dict_closing_order

		return result


	def get_turnovers(self):
		if self._turnovers == []:
			return "NONE"

		result = ""

		for t in self._turnovers:
			if t == "long":
				result += Fore.GREEN + "+" + Style.RESET_ALL

			elif t == "short":
				result += Fore.RED + "+" + Style.RESET_ALL

			else:
				result += Fore.RED + "X" + Style.RESET_ALL

		return result


	def _cancel_open_orders(self):
		while self._open_orders != []:
			for order in self._open_orders:
				printError("Cancelling order %s" % order["orderNumber"])
				try:
					self._client.cancelOrder(order["orderNumber"])

				except Exception, e:
					printError("Error cancelling order: %s" % e.message)

			self._open_orders = do(
				self._client.returnOpenOrders,
				self._pair
			)
		
		self._opening_order = {}
		self._closing_order = {}


	def _move_order(self, orderNumber, rate, amount):
		try:
			temp = self._client.moveOrder(orderNumber, rate, amount)
			return temp["orderNumber"]

		except Exception, e:
			printError("Error moving order: %s" % e.message)
			return orderNumber



	def _get_order(self, order):
		if self._open_orders == []:
			return {}

		if order == {} or order == None:
			return {}

		orderNumber = order.get("orderNumber")
		if orderNumber == None:
			return {}

		for order in self._open_orders:
			if str(order["orderNumber"]) == str(orderNumber):
				return order

		return {}


	def _force_close(self, reason):
		try:
			self._client.closeMarginPosition(self._pair)
			self._cancel_open_orders()

			return "Margin position force closed: %s" % reason
				
		except Exception, e:
			return "Error closing margin position: %s" % e.message 	


	def _create_closing_order(self):
		dict_closing_order = {}

		if self._status == "long":
			dict_closing_order["func"] = self._client.marginSell
			dict_closing_order["rate"] = float(self._margin_position["basePrice"]) * self._profit_margin

		elif self._status == "short":
			dict_closing_order["func"] = self._client.marginBuy
			dict_closing_order["rate"] = float(self._margin_position["basePrice"]) * (2 - self._profit_margin)

		else:
			printError("_create_closing_order called when position is none")
			quit()

		dict_closing_order["amount"] = abs(float(self._margin_position["amount"]))
		dict_closing_order["total"] = dict_closing_order["amount"] * dict_closing_order["rate"]

		return dict_closing_order


	def _create_opening_order(self, ema, lowest_ask, highest_bid):
			dict_opening_order = {}

			opening_rate_short = float(ema) * self._short_margin
			opening_rate_long = float(ema) * self._long_margin

			delta_short = getDelta(opening_rate_short, lowest_ask)
			delta_long = getDelta(opening_rate_long, highest_bid)


			delta_short = getDelta(opening_rate_short, lowest_ask)
			delta_long = getDelta(opening_rate_long, highest_bid)

			if delta_long <= delta_short:
				dict_opening_order["func"] = self._client.marginBuy
				dict_opening_order["rate"] = opening_rate_long
				dict_opening_order["delta"] = delta_long
				dict_opening_order["type"] = "LONG"

				if float(highest_bid) <= opening_rate_long:
					dict_opening_order["delta"] = 0
			
			else:
				dict_opening_order["func"] = self._client.marginSell
				dict_opening_order["rate"] = opening_rate_short
				dict_opening_order["delta"] = delta_short
				dict_opening_order["type"] = "SHORT"

				if float(lowest_ask) >= opening_rate_short:
					dict_opening_order["delta"] = 0

			if self._status == "none":
				dict_opening_order["amount"] = getAmount(self._balance, dict_opening_order["rate"])

			else:
				dict_opening_order["amount"] = getAmount(self._balance - abs(float(self._margin_position["total"])), dict_opening_order["rate"])

			if dict_opening_order["amount"] == -1:
				dict_opening_order["delta"] = 9999999999

			dict_opening_order["total"] = dict_opening_order["amount"] * dict_opening_order["rate"]

			if self._last_opening_dict == {}:
				self._last_opening_dict = dict_opening_order

			return dict_opening_order


	def _check_API(self):
		apiPath = "./config/API.ini"

		if not os.path.isfile(apiPath):
			with open(apiPath, "w+") as f:
				apiKey = raw_input("Enter your Poloniex API key: ").strip()
				secret = raw_input("Enter your Poloniex API secret: ").strip()
				f.writelines(["APIKey=%s" % apiKey,  "\nSecret=%s" % secret])

		else:
			with open(apiPath, 'r') as f:
				lines = f.readlines()
				apiKey = lines[0].split('=')[1].strip()
				secret = lines[1].split('=')[1].strip()

		printSuccess("Using API Key: %s" % apiKey)
		return poloniex.Poloniex(apiKey, secret)


	def _check_balance(self):
		accountBalance = float(do(self._client.returnTradableBalances)[self._pair]["BTC"])

		if accountBalance < 0.1:
			printError("Not enough BTC to trade")
			quit()

		printSuccess("Margin account tradable balance: %s BTC" % accountBalance)
		printSuccess("Using: %s BTC" % (self._balance_max * accountBalance))

		return self._balance_max * accountBalance



	def _filter_orders(self, key, value):
		filtered_orders = []

		self._open_orders = do(
			self._client.returnOpenOrders,
			self._pair
		)

		for order in self._open_orders:
			if str(order[str(key)]) == str(value):
				filtered_orders.append(order)

		return filtered_orders
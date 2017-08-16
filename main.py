import datetime, time, sys, pip, imp, os

try:
	imp.find_module("poloniex")
except ImportError:
	print "The 'poloniex' package is not installed. Attempting to install..."
	pip.main(["install", "https://github.com/s4w3d0ff/python-poloniex/archive/v0.4.3.zip"])

try:
	imp.find_module("colorama")
except ImportError:
	print "The 'colorama' package is not installed. Attempting to install..."
	pip.main(["install", "colorama"])

for dir in ["./config/"]:
	if not os.path.exists(dir):
		os.makedirs(dir)

import poloniex, settings, polopublic, poloprivate
from utils import *


BOT_PAIR = sys.argv[1].upper()
BOT_CYCLE = 1
BOT_COMMENT = ""

settings = settings.Settings(BOT_PAIR)
config = settings.settings
polopublic = polopublic.PoloPublic(BOT_PAIR, config)
poloprivate = poloprivate.PoloPrivate(BOT_PAIR, config)

while True:
	settings.refresh()
	config = settings.settings
	polopublic.refresh(config)
	poloprivate.refresh(config)

	current_ema = getEMAList(polopublic.data_chart, config["ema"], polopublic.data_ticker["last"])[-1]

	if poloprivate.status == "none":
		BOT_COMMENT = poloprivate.open(
			current_ema,
			polopublic.data_ticker["lowestAsk"],
			polopublic.data_ticker["highestBid"]
		)

	else:
		BOT_COMMENT = poloprivate.close()
		BOT_COMMENT += poloprivate.update_open(
			current_ema,
			polopublic.data_ticker["lowestAsk"],
			polopublic.data_ticker["highestBid"]
		)

	printSuccess("\n--------- Cycle: %s ----------" % BOT_CYCLE)
	printHeader("---------- %s ----------" % BOT_PAIR)
	if poloprivate.status == "none":
		printInfo("Last closing time .............: %s" % poloprivate.closing_time)
		printInfo("Current EMA ...................: %s" % formatFloat(current_ema))
		printInfo("Opening price .................: %s" % formatFloat(poloprivate.last_opening_dict["rate"]))
		printInfo("Target position ...............: %s" % poloprivate.last_opening_dict["type"])
		printInfo("Status ........................: %s >> %s" % (poloprivate.status.upper(), BOT_COMMENT))
		printInfo("Turnovers .....................: %s" % poloprivate.get_turnovers())

	else:
		printSuccess("Opening time ..................: %s" % poloprivate.opening_time)
		printSuccess("Base price ....................: %s" % formatFloat(poloprivate.margin_position["basePrice"]))
		printSuccess("Closing price .................: %s" % formatFloat(poloprivate.last_closing_dict["rate"]))
		printSuccess("Status ........................: %s >> %s" % (poloprivate.status.upper(), BOT_COMMENT))
		printSuccess("Turnovers .....................: %s" % poloprivate.get_turnovers())

	BOT_CYCLE += 1

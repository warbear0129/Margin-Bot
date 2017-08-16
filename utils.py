import time
from colorama import init, Fore, Style

def printHeader(msg):
    print Fore.CYAN + str(msg) + Style.RESET_ALL


def printInfo(msg):
    print Fore.YELLOW + str(msg) + Style.RESET_ALL


def printSuccess(msg):
    print Fore.GREEN + str(msg) + Style.RESET_ALL


def printError(msg):
    print Fore.RED + str(msg) + Style.RESET_ALL

def log(pair, msg):
    filename = "./logs/%s.log" % pair
    with open(filename, "a") as f:
            f.write(msg + "\t\n")

def formatFloat(f):
	return '{0:.8f}'.format(float(f))

def do(f, *args):
	time.sleep(0.2)

	result = None
	while result == None:
		try:
			result = f(*args)

		except Exception, e:
			printError("Error: %s" % e.message)
			time.sleep(0.2)

	return result

def getEMAList(chart_data, n, last_price):
	emaList = [float(chart_data.pop(0)["weightedAverage"])]
	chart_data[-1]["close"] = last_price
	k = (2.0 / (n + 1))

	for i in range(len(chart_data)):
		close = float(chart_data[i]["close"])
		y = emaList[i]
		n = (close * k) + (y * (1 - k))
		emaList.append(n)

	return emaList

def getAmount(total, rate):
	if total == 0 or rate == 0:
		return -1

	return round(float(str(total)) / float(str(rate)), 8)

def getDelta(x, y):
	if x == 0 or y == 0:
		return 99999999999
	
	numList = [float(x), float(y)]
	return (( max(numList) / min(numList) ) - 1 ) * 100

init()

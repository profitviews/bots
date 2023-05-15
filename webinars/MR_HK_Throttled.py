from profitview import Link, http, logger
import time
import talib
import numpy as np


class Throttle:
    NS = 1e+9
    last = time.time_ns()
    frequency = 1
    
		
def throttle(func):
    def throttle_wrapper(*args, **kwargs):
		if time.time_ns() - Throttle.last < Throttle.NS/Throttle.frequency:
			# Throttled - don't do anything
			return
        value = func(*args, **kwargs)
		logger.info(f"Executed: {func.__name__=} returning {value}")
		Throttle.last = time.time_ns()  # Reset throttle                
		return value
    return throttle_wrapper


class Strategy:
    VENUE = 'BitMEX_Bot'
    REVERSION = 2.5
    LOOKBACK = 50
    MIN_SIZE = 100.0
	HK_PROXY = {
		'XBTUSD': { 'sym': 'XBT_USDT', 'min': 50_000}
	}

    
class Trading(Link):
    def __init__(self):
        super().__init__()
        self.prices = []
		self.elements = 0
		self.mean = 0

	@throttle
    def create_market_order(self, venue, sym, side, size):
        return super().create_market_order(venue, sym, side, size)

    def trade_update(self, src, sym, data):
		proxy = Strategy.HK_PROXY[sym]
        self.prices.append(newPrice := data["price"])
        if self.elements < Strategy.LOOKBACK:
            # Until we have enough data for the mean
            self.mean = (self.elements*self.mean + newPrice)/(self.elements + 1)
            self.elements += 1
        else:  # Move and recalculate mean
            self.mean += (newPrice - self.prices[0])/self.elements
            self.prices = self.prices[1:]
            stddev = talib.STDDEV(np.array(self.prices))[4]
            stdReversion = Strategy.REVERSION*stddev
            if newPrice > self.mean + stdReversion:  # Upper extreme - Sell!
                self.create_market_order(Strategy.VENUE, proxy['sym'], "Sell", proxy['min'])
            if newPrice < self.mean - stdReversion:  # Lower extreme - Buy!
                self.create_market_order(Strategy.VENUE, proxy['sym'], "Buy", proxy['min'])

# This code is designed for insertion into the ProfitView Trading Bots tab
# It is provided as an example of a Trading Bot that should run
# It is *not* expected to trade effectively.  Instead, it will likely lose
# money.
#
# WARNING: use this code AT YOUR OWN RISK.

from profitview import Link, logger
import talib
import numpy as np


class Strategy:
    VENUE = 'BitMEX_Bot'
    REVERSION = 2.5
    LOOKBACK = 50
    SIZE = 100.0

    
class Trading(Link):
    def __init__(self):
        super().__init__()
        self.prices = []
		self.elements = 0
		self.mean = 0

    def trade_update(self, src, sym, data):
        """Event: receive market trades from subscribed symbols"""
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
                self.create_market_order(Strategy.VENUE, sym, "Sell", Strategy.SIZE)
            if newPrice < self.mean - stdReversion:  # Lower extreme - Buy!
                self.create_market_order(Strategy.VENUE, sym, "Buy", Strategy.SIZE)
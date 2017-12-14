"""
MD5: 7ea8d5fe1a5a1a4741bff19a17029fb5
"""

# pylint: disable=C0321,C0103,W0613,R0201,R0913
try: QCAlgorithm
except NameError: from mocked import OrderType

from market import Order, Portfolio

class Algorithm(object):

    # Methods to ignore.
    def __getattr__(self, attr):
        """Delegate everything else to parent."""
        if hasattr(self._parent, attr):
            return getattr(self._parent, attr)
        else:
            raise AttributeError, attr

    def __init__(self, parent, broker, cash, name="anonymous"):
        self._parent = parent
        self.broker = broker
        self._name = name
        self.Portfolio = Portfolio(parent=parent, cash=cash)
        self.Initialize()

    def __str__(self):
        return "[%s] %s" % (self._name, str(self.Portfolio))

    def _tag(self, tag):
        return "%s: %s" % (self._name, tag) if tag else self._name

    ######################################################################
    def CoarseSelectionFunction(self, coarse): return []
    def FineSelectionFunction(self, fine): return []
    def OnData(self, args): pass
    def OnDividend(self): pass
    def OnEndOfDay(self): pass
    def OnEndOfAlgorithm(self): pass
    def OnSecuritiesChanged(self, changes): pass
    def Initialize(self): pass
    def SetStartDate(self, *args, **kwargs): pass
    def SetEndDate(self, *args, **kwargs): pass
    def SetCash(self, cash): pass

    def Log(self, data):
        self._parent.Log("%s - %s - %s" % (self.Time, self._name, data))

    def Debug(self, data):
        self._parent.Debug("%s - %s - %s" % (self.Time, self._name, data))

    def SetHoldings(self, symbol, target_allocation, liquidate_existing_holdings=False, tag=""):
        orders = self.Portfolio.getOrdersForTargetAllocation(symbol, target_allocation, tag=self._tag(tag))
        for order in orders:
            self.broker.addOrder(order)

    def MarketOrder(self, symbol, quantity, tag=""):
        return self.broker.addOrder(Order(self.Portfolio, symbol, quantity, order_type=OrderType.Market,
                                          tag=self._tag(tag)))

    def LimitOrder(self, symbol, quantity, limit_price, tag=""):
        return self.broker.addOrder(Order(self.Portfolio, symbol, quantity, order_type=OrderType.Limit,
                                          limit_price=limit_price, tag=self._tag(tag)))

    def StopMarketOrder(self, symbol, quantity, stop_price, tag=""):
        return self.broker.addOrder(Order(self.Portfolio, symbol, quantity, order_type=OrderType.StopMarket,
                                          stop_price=stop_price, tag=self._tag(tag)))

    def StopLimitOrder(self, symbol, quantity, stop_price, limit_price, tag=""):
        return self.broker.addOrder(Order(self.Portfolio, symbol, quantity, order_type=OrderType.StopLimit,
                                          stop_price=stop_price, limit_price=limit_price, tag=self._tag(tag)))

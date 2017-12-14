"""
MD5: 89feb968fa74a97a8f276212a59a7fa6
"""

# pylint: disable=C0321,C0103,W0613,R0201,R0913
try: QCAlgorithm
except NameError: from mocked import OrderType

from market import Order, Portfolio

class Algorithm(object):

    # Methods to ignore.
    def __getattr__(self, attr):
        """Delegate everything else to parent."""
        if hasattr(self.__parent, attr):
            return getattr(self.__parent, attr)
        else:
            raise AttributeError, attr

    def __init__(self, parent, broker, cash, name="anonymous"):
        self.__parent = parent
        self.__name = name
        self.Portfolio = Portfolio(parent=parent, broker=broker, cash=cash)
        self.Initialize()

    def __str__(self):
        return "[%s] %s" % (self.__name, str(self.Portfolio))

    def __tag(self, tag):
        return "%s: %s" % (self.__name, tag) if tag else self.__name

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
        self.__parent.Log("%s - %s - %s" % (self.Time, self.__name, data))

    def Debug(self, data):
        self.__parent.Debug("%s - %s - %s" % (self.Time, self.__name, data))

    def SetHoldings(self, symbol, target_allocation, liquidate_existing_holdings=False, tag=""):
        orders = self.Portfolio.getOrdersForTargetAllocation(symbol, target_allocation, tag=self.__tag(tag))
        for order in orders:
            self.Portfolio.addOrder(order)

    def MarketOrder(self, symbol, quantity, tag=""):
        order = Order(self.Portfolio, symbol, quantity, order_type=OrderType.Market, tag=self.__tag(tag))
        return self.Portfolio.addOrder(order)

    def LimitOrder(self, symbol, quantity, limit_price, tag=""):
        order = Order(self.Portfolio, symbol, quantity, order_type=OrderType.Limit, limit_price=limit_price,
                      tag=self.__tag(tag))
        return self.Portfolio.addOrder(order)

    def StopMarketOrder(self, symbol, quantity, stop_price, tag=""):
        order = Order(self.Portfolio, symbol, quantity, order_type=OrderType.StopMarket,
                      stop_price=stop_price, tag=self.__tag(tag))
        return self.Portfolio.addOrder(order)

    def StopLimitOrder(self, symbol, quantity, stop_price, limit_price, tag=""):
        order = Order(self.Portfolio, symbol, quantity, order_type=OrderType.StopLimit,
                      stop_price=stop_price, limit_price=limit_price, tag=self.__tag(tag))
        return self.Portfolio.addOrder(order)

    def Liquidate(self, symbol=None):
        self.Portfolio.Liquidate(symbol)

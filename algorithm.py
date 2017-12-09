"""
MD5: 21ddd616b3303902b42e9edca9ea13c1
"""


try: QCAlgorithm
except NameError: from mocked import OrderType

from market import Order, Portfolio

# pylint: disable=W0613
class Algorithm(object):

    # Methods to ignore.
    IGNORED_METHODS = ['Initialize', 'SetCash', 'SetStartDate', 'SetEndDate']
    def __getattr__(self, attr):
        """Delegate everything else to parent."""
        if attr in Algorithm.IGNORED_METHODS:
            self.Debug(">>> %s -- call ignored" % attr)
            return self.dummy.__call__
        elif hasattr(self._parent, attr):
            self.Debug(">>> %s" % attr)
            return getattr(self._parent, attr)
        else:
            raise AttributeError, attr

    def dummy(self, *args, **kwargs):
        pass

    def Log(self, data): self._parent.Log("[%s] %s" % (self.name, data))
    def Debug(self, data): self._parent.Debug("[%s] %s" % (self.name, data))
    # def Initialize(self): pass
    def CoarseSelectionFunction(self, coarse): return []
    def FineSelectionFunction(self, fine): return []
    def OnData(self, args): pass
    def OnDividend(self): pass
    def OnEndOfDay(self): pass
    def OnEndOfAlgorithm(self): pass
    def OnSecuritiesChanged(self, changes): pass

    def __init__(self, parent, broker, cash, name="anonymous"):
        self._parent = parent
        self.broker = broker
        self.name = name

        # Override QuantConnect's Portfolio
        self.Portfolio = Portfolio(parent=parent, cash=cash)

        self.Initialize()


    ######################################################################

    def SetHoldings(self, symbol, target_allocation,
                    liquidate_existing_holdings=False):
        orders = self.Portfolio.getOrdersForTargetAllocation(symbol, target_allocation)
        for order in orders:
            self.broker.addOrder(order)


    def MarketOrder(self, symbol, quantity, tag=""):
        return self.broker.addOrder(Order(self.Portfolio, symbol, quantity,
                                          order_type=OrderType.Market, tag=tag))

    def LimitOrder(self, symbol, quantity, limit_price, tag=""):
        return self.broker.addOrder(Order(self.Portfolio, symbol, quantity,
                                          order_type=OrderType.Limit,
                                          limit_price=limit_price, tag=tag))

    def StopMarketOrder(self, symbol, quantity, stop_price, tag=""):
        return self.broker.addOrder(Order(self.Portfolio, symbol, quantity,
                                          order_type=OrderType.StopMarket,
                                          stop_price=stop_price, tag=tag))

    def StopLimitOrder(self, symbol, quantity, stop_price, limit_price, tag=""):
        return self.broker.addOrder(Order(self.Portfolio, symbol, quantity,
                                          order_type=OrderType.StopLimit,
                                          stop_price=stop_price,
                                          limit_price=limit_price, tag=tag))

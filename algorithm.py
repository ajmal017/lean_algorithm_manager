"""
MD5: 9e688c13da8cdae0fa305b0d485342c3
"""

# pylint: disable=C0321,C0103,W0613,R0201,R0913, R0904
try: QCAlgorithm
except NameError: from mocked import OrderType

from market import Order, Portfolio

class SimpleAlgorithm(object):

    def __init__(self, parent, broker, cash, name="anonymous"):
        self._parent = parent
        self.Name = name
        self.Initialize()

    def __getattr__(self, attr):
        """Delegate to parent."""
        if hasattr(self._parent, attr):
            # if attr not in ['Log', 'Debug', 'Error']:
            self._parent.Log("Delegating to parent: %s" % attr)
            return getattr(self._parent, attr)
        else:
            raise AttributeError, attr

    @property
    def Performance(self):
        return 0.0

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

    def Log(self, message):
        self._parent.Log("%s [%s] %s" % (self.Time, self.Name, message))

    def Debug(self, message):
        self._parent.Debug("%s [%s] %s" % (self.Time, self.Name, message))

    def Error(self, message):
        self._parent.Error("%s [%s] %s" % (self.Time, self.Name, message))

    # def MarketOrder(self, symbol, quantity, tag=""):
    #     self.Log("MarketOrder(%s, %f)" % (symbol.Value, quantity))
    #     return self._parent.MarketOrder(symbol, quantity, tag)

    # def LimitOrder(self, symbol, quantity, limit_price, tag=""):
    #     self.Log("LimitOrder(%s, %f)" % (symbol.Value, quantity))
    #     return self._parent.LimitOrder(symbol, quantity, limit_price, tag)

    # def StopMarketOrder(self, symbol, quantity, stop_price, tag=""):
    #     self.Log("StopMarketOrder(%s, %f)" % (symbol.Value, quantity))
    #     return self._parent.StopMarketOrder(symbol, quantity, stop_price, tag)

    # def StopLimitOrder(self, symbol, quantity, stop_price, limit_price, tag=""):
    #     self.Log("StopLimitOrder(%s, %f)" % (symbol.Value, quantity))
    #     return self._parent.StopLimitOrder(symbol, quantity, stop_price, limit_price, tag)

    # def MarketOnOpenOrder(self, symbol, quantity, tag=""):
    #     self.Log("MarketOnOpenOrder(%s, %f)" % (symbol.Value, quantity))
    #     return self._parent.MarketOnOpenOrder(symbol, quantity, tag)

    # def MarketOnCloseOrder(self, symbol, quantity, tag=""):
    #     self.Log("MarketOnCloseOrder(%s, %f)" % (symbol.Value, quantity))
    #     return self._parent.MarketOnCloseOrder(symbol, quantity, tag)

    # def OptionExerciseOrder(self, symbol, quantity, tag=""):
    #     self.Log("OptionExerciseOrder(%s, %f)" % (symbol.Value, quantity))
    #     return self._parent.OptionExerciseOrder(symbol, quantity, tag)

    # def SetHoldings(self, symbol, percentage, liquidateExistingHoldings=False, tag=""):
    #     self.Log("SetHoldings(%s, %f)" % (symbol.Value, percentage))
    #     return self._parent.SetHoldings(symbol, percentage, liquidateExistingHoldings, tag)

    # def Liquidate(self, symbol=None, tag=""):
    #     self.Log("Liquidate(%s, %f)" % (symbol.Value, percentage))
    #     return self._parent.MarketOrder(symbol, quantity, tag)

class Algorithm(SimpleAlgorithm):

    def __init__(self, parent, broker, cash, name="anonymous"):
        self._parent = parent
        self.Securities = {}
        self.Name = name
        self.Portfolio = Portfolio(parent=parent, broker=broker, cash=cash)
        self.Initialize()

    def __getattr__(self, attr):
        """Delegate to parent."""
        if hasattr(self._parent, attr):
            # if attr not in ['Log', 'Debug', 'Error']:
            # self._parent.Log("Delegating to parent: %s" % attr)
            return getattr(self._parent, attr)
        else:
            raise AttributeError, attr

    def __str__(self):
        return "[%s] %s" % (self.Name, str(self.Portfolio))

    def _tag(self, tag):
        return "%s: %s" % (self.Name, tag) if tag else self.Name

    ######################################################################
    @property
    def Performance(self):
        return self.Portfolio.Performance

    def AddEquity(self, ticker, resolution):
        equity = self._parent.AddEquity(ticker, resolution)
        self.Securities[ticker] = equity.Symbol
        return equity

    def _fetchSymbol(self, ticker):
        if ticker is None or type(ticker) is Symbol:
            return ticker
        return self.Securities[ticker]

    def _createOrder(self, symbol, quantity, order_type, **kwargs):
        symbol = self._fetchSymbol(symbol)
        order = Order(self.Portfolio, symbol, quantity, order_type, kwargs)
        return self.Portfolio.AddOrder(order)

    def MarketOrder(self, symbol, quantity, tag=""):
        symbol = self._fetchSymbol(symbol)
        self.Log("MarketOrder(%s, %f)" % (symbol.Value, quantity))
        return self._createOrder(symbol, quantity, OrderType.Market, tag=self._tag(tag))

    def LimitOrder(self, symbol, quantity, limit_price, tag=""):
        symbol = self._fetchSymbol(symbol)
        self.Log("LimitOrder(%s, %f)" % (symbol.Value, quantity))
        return self._createOrder(symbol, quantity, OrderType.Limit, limit_price=limit_price,
                                 tag=self._tag(tag))

    def StopMarketOrder(self, symbol, quantity, stop_price, tag=""):
        symbol = self._fetchSymbol(symbol)
        self.Log("StopMarketOrder(%s, %f)" % (symbol.Value, quantity))
        return self._createOrder(symbol, quantity, OrderType.Limit, stop_price=stop_price,
                                 tag=self._tag(tag))

    def StopLimitOrder(self, symbol, quantity, stop_price, limit_price, tag=""):
        symbol = self._fetchSymbol(symbol)
        self.Log("StopLimitOrder(%s, %f)" % (symbol.Value, quantity))
        return self._createOrder(symbol, quantity, OrderType.Limit, stop_price=stop_price,
                                 limit_price=limit_price, tag=self._tag(tag))

    def MarketOnOpenOrder(self, symbol, quantity, tag=""):
        symbol = self._fetchSymbol(symbol)
        self.Log("MarketOnOpenOrder(%s, %f)" % (symbol.Value, quantity))
        return self._createOrder(symbol, quantity, OrderType.MarketOnOpen, tag=self._tag(tag))

    def MarketOnCloseOrder(self, symbol, quantity, tag=""):
        symbol = self._fetchSymbol(symbol)
        self.Log("MarketOnCloseOrder(%s, %f)" % (symbol.Value, quantity))
        return self._createOrder(symbol, quantity, OrderType.MarketOnClose, tag=self._tag(tag))

    def OptionExerciseOrder(self, symbol, quantity, tag=""):
        symbol = self._fetchSymbol(symbol)
        self.Log("OptionExerciseOrder(%s, %f)" % (symbol.Value, quantity))
        return self._createOrder(symbol, quantity, OrderType.OptionExercise, tag=self._tag(tag))

    def SetHoldings(self, symbol, percentage, liquidateExistingHoldings=False, tag=""):
        symbol = self._fetchSymbol(symbol)
        self.Log("SetHoldings(%s, %f)" % (symbol.Value, percentage))
        if liquidateExistingHoldings:
            to_liquidate = [s for s, p in self.Portfolio.iteritems() if s != symbol and p.Quantity > 0]
            for s in to_liquidate:
                self.Portfolio.Liquidate(symbol=s, tag=self._tag(tag))

        order = self.Portfolio.GenerateOrder(symbol, percentage, tag=self._tag(tag))
        self.Log(order)
        self.Portfolio.AddOrder(order)

    def Liquidate(self, symbol=None, tag=""):
        symbol = self._fetchSymbol(symbol)
        if symbol is None:
            self.Log("Liquidate()")
        else:
            self.Log("Liquidate(%s)" % symbol.Value)
        self.Portfolio.Liquidate(symbol=symbol, tag=self._tag(tag))

"""
MD5: ba40d0da71d1fbebd2679eae3bbfa601
"""

from datetime import timedelta

# pylint: disable=C0321,C0103,W0613,R0201,R0913, R0904, C0111
try: QCAlgorithm
except NameError: from mocked import TradeBarConsolidator, OrderType, Symbol, QCAlgorithm

from algorithm_manager import Singleton
from decorators import accepts, convert_to_symbol
from market import Portfolio, InternalOrder, InternalSecurity, Securities


class SimpleAlgorithm(object):
    def __init__(self, cash, name="anonymous", initialize=True, broker=None):
        self.Name = name
        if initialize:
            self.Initialize()

    def __str__(self):
        return "[%s] %s" % (self.Name, str(self.Portfolio))

    def __getattr__(self, attr):
        """Delegate to parent."""
        if hasattr(Singleton, attr):
            return getattr(Singleton, attr)
        else:
            raise AttributeError(attr)

    def post(self):
        pass

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
    def OnOrderEvent(self, order_event): pass
    def Initialize(self): self.Debug("Initialize call ignored")
    def SetCash(self, cash): self.Debug("SetCash call ignored")
    def SetStartDate(self, year, month, day): self.Debug("SetStartDate call ignored")
    def SetEndDate(self, year, month, day): self.Debug("SetStartDate call ignored")
    def SetWarmUp(self, period): Singleton.SetWarmUpFromAlgorithm(period)
    def Log(self, message): Singleton.Log("LOG [%s] %s" % (self.Name, message))
    def Debug(self, message): Singleton.Debug("DEBUG [%s] %s" % (self.Name, message))
    def Info(self, message): Singleton.Info("INFO [%s] %s" %(self.Name, message))
    def Error(self, message): Singleton.Error("ERROR [%s] %s" % (self.Name, message))
    def TryToFillOnOrderEvent(self, order_event): return True


class Algorithm(SimpleAlgorithm):
    def __init__(self, broker, cash, name="anonymous", options={}):
        super(Algorithm, self).__init__(cash=cash, name=name, initialize=False)
        self.Options = options
        self.Securities = Securities()
        self.Portfolio = Portfolio(broker=broker, cash=cash, name=name)
        self.Portfolio.SetupLog(self)
        self.Initialize()

    def post(self):
        self.Portfolio.Broker.executeOrders()

    def _tag(self, tag):
        return "%s: %s" % (self.Name, tag) if tag else self.Name

    @property
    def Performance(self):
        return self.Portfolio.Performance

    # Can't use this
    # @accepts(self=object, order_event=OrderEvent)
    def TryToFillOnOrderEvent(self, order_event):
        self.Debug("OrderID: {}".format(order_event.OrderId))
        self.Debug("Submitted: {}".format(self.Portfolio.Broker.submitted))
        order = self.Portfolio.Broker.submitted.pop(order_event.OrderId, None)
        if order:
            self.Debug("ORDER: {0}".format(order))
            order.Portfolio.ProcessOrderEvent(order_event, order)
            return True
        return False

    def CreateRollingWindow(self, symbol, window_size):
        rolling_window = RollingWindow[TradeBar](window_size)
        consolidator = TradeBarConsolidator(timedelta(1))
        consolidator.DataConsolidated += lambda _, bar: rolling_window.Add(bar)
        self.SubscriptionManager.AddConsolidator(symbol, consolidator)
        return rolling_window

    ######################################################################
    @accepts(self=object, ticker=(str, Symbol), resolution=int)
    def AddEquity(self, ticker, resolution):
        equity = Singleton.AddEquity(ticker, resolution)
        self.Securities[equity.Symbol] = InternalSecurity(equity)
        return equity

    @accepts(self=object, security_type=int, ticker=(str, Symbol), resolution=int)
    def AddSecurity(self, security_type, ticker, resolution):
        security = Singleton.AddSecurity(security_type, ticker, resolution)
        self.Securities[security.Symbol] = InternalSecurity(security)
        return security

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def _createOrder(self, symbol, quantity, order_type, **kwargs):
        order = InternalOrder(portfolio=self.Portfolio, symbol=symbol, quantity=quantity,
                              order_type=order_type, **kwargs)
        return self.Portfolio.AddOrder(order)

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def MarketOrder(self, symbol, quantity, tag=""):
        self.Debug("MarketOrder(%s, %f)" % (symbol, quantity))
        return self._createOrder(symbol, quantity, OrderType.Market, tag=self._tag(tag))

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def LimitOrder(self, symbol, quantity, limit_price, tag=""):
        self.Debug("LimitOrder(%s, %f)" % (symbol, quantity))
        return self._createOrder(symbol, quantity, OrderType.Limit, limit_price=limit_price,
                                 tag=self._tag(tag))

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def StopMarketOrder(self, symbol, quantity, stop_price, tag=""):
        self.Debug("StopMarketOrder(%s, %f)" % (symbol, quantity))
        return self._createOrder(symbol, quantity, OrderType.Limit, stop_price=stop_price,
                                 tag=self._tag(tag))

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def StopLimitOrder(self, symbol, quantity, stop_price, limit_price, tag=""):
        self.Debug("StopLimitOrder(%s, %f)" % (symbol, quantity))
        return self._createOrder(symbol, quantity, OrderType.Limit, stop_price=stop_price,
                                 limit_price=limit_price, tag=self._tag(tag))

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def MarketOnOpenOrder(self, symbol, quantity, tag=""):
        self.Debug("MarketOnOpenOrder(%s, %f)" % (symbol, quantity))
        return self._createOrder(symbol, quantity, OrderType.MarketOnOpen, tag=self._tag(tag))

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def MarketOnCloseOrder(self, symbol, quantity, tag=""):
        self.Debug("MarketOnCloseOrder(%s, %f)" % (symbol, quantity))
        return self._createOrder(symbol, quantity, OrderType.MarketOnClose, tag=self._tag(tag))

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def OptionExerciseOrder(self, symbol, quantity, tag=""):
        self.Debug("OptionExerciseOrder(%s, %f)" % (symbol, quantity))
        return self._createOrder(symbol, quantity, OrderType.OptionExercise, tag=self._tag(tag))

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def SetHoldings(self, symbol, percentage, liquidateExistingHoldings=False, tag=""):
        self.Debug("SetHoldings(%s, %f)" % (symbol, percentage))
        if liquidateExistingHoldings:
            to_liquidate = [s for s, p in iter(self.Portfolio.items()) if s != symbol and p.Quantity > 0]
            for s in to_liquidate:
                self.Portfolio.Liquidate(symbol=s, tag=self._tag(tag))

        order = self.Portfolio.GenerateOrder(symbol, percentage, tag=self._tag(tag))
        self.Portfolio.AddOrder(order)

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def Liquidate(self, symbol=None, tag=""):
        tag = 'Liquidated' if not tag else tag + ': Liquidated'
        if symbol is None:
            self.Debug("Liquidate()")
        else:
            self.Debug("Liquidate(%s)" % symbol)
        self.Portfolio.Liquidate(symbol=symbol, tag=self._tag(tag))

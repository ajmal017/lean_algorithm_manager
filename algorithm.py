# pylint: disable=C0321,C0103,W0613,R0201,R0913, R0904, C0111
try: QCAlgorithm
except NameError:
    from mocked import TradeBarConsolidator, OrderType, OrderEvent, Symbol, SecurityType, QCAlgorithm, Resolution

import math
from datetime import timedelta
from decorators import accepts, convert_to_symbol
from market import Portfolio, InternalOrder, Broker, BenchmarkSymbol
from singleton import Singleton, Email


class AlgorithmManager(QCAlgorithm):

    @accepts(self=object, algorithms=list, reserve=float, reset=bool, plot_orders=bool, plot_value=bool, plot_allocation=bool, email_address=str)
    def registerAlgorithms(self, algorithms, reserve=0.0, reset=True, plot_orders=True, plot_value=True, plot_allocation=True, email_address=None):
        if Singleton.Broker is None:
            Singleton.Broker = Broker()

        assert len(algorithms) > 0

        if not hasattr(self, '_benchmark'):
            self._benchmark = None

        self.__algorithms = algorithms
        self.__reserve = reserve
        self.__reset = reset
        self.__email_address = email_address

        self.__year = None
        self.__month = None
        self.__plot_every_n_days = 1 if self.LiveMode else 5
        self.__plot_every_n_days_i = 0
        self.__plot_orders = plot_orders
        self.__plot_value = plot_value
        self.__plot_allocation = plot_allocation
        self.__initial_cost = 0.0
        self.__cost = 0.0

        total_allocation = 0.0
        algorithms_allocation = 1.0 - self.__reserve
        for i in self.__algorithms:
            # automatically set allocation if set to None
            if i.Allocation is None:
                i.Allocation = algorithms_allocation / len(algorithms)
            total_allocation += i.Allocation

        assert total_allocation <= 1.00, \
            f"Total allocation exceeds 100%: {round(100 * total_allocation, 1)}%"

        plot = Chart('Annual Saw Tooth Returns')
        for i in self.__algorithms:
            plot.AddSeries(Series(i.Name, SeriesType.Line, '%'))
        if self._benchmark:
            plot.AddSeries(Series(self._benchmark.Name, SeriesType.Line, '%'))
        self.AddChart(plot)

        if self.__plot_orders:
            plot = Chart('Orders')
            for i in self.__algorithms:
                plot.AddSeries(Series(i.Name, SeriesType.Line, ''))
            self.AddChart(plot)

        if self.__plot_value:
            plot = Chart("Value")
            for i in self.__algorithms:
                plot.AddSeries(Series(i.Name, SeriesType.Line, '$'))
                self.Plot("Value", i.Name, i.Portfolio.TotalPortfolioValue)
            self.AddChart(plot)

        if self.__plot_allocation:
            plot = Chart("Allocation")
            for i in self.__algorithms:
                plot.AddSeries(Series(i.Name, SeriesType.Line, '%'))
                self.Plot("Allocation", i.Name, round(100.0 * i.Allocation, 1))
            self.AddChart(plot)

        if self.__email_address:
            for i in self.__algorithms:
                i.Email.SetEmailAddress(self.__email_address)
                i.Email.AppendText("Algorithm started")
                i.Email.Send(f"{i.Name} (Started)")


    def ResetPlot(self):
        self.__cost = 0.0
        self.__plot_every_n_days_i == 0

        for i in self.__algorithms:
            cost = i.Portfolio.TotalPortfolioValue
            self.__cost += cost
            i.Portfolio.SetCost(cost)
            i.TotalOrders = 0

        if self._benchmark:
            self._benchmark.Reset()

    def ResetOrders(self):
        for i in self.__algorithms:
            i.TotalOrders = 0

    def SetCash(self, cash):
        super().SetCash(cash)
        self.__initial_value = cash

    def SetBenchmark(self, benchmark, security_type=SecurityType.Equity):
        self._benchmark = BenchmarkSymbol(benchmark, security_type=security_type)

    def CoarseSelectionFunction(self, coarse):
        symbols = []
        for i in self.__algorithms:
            symbols.extend(i.CoarseSelectionFunction(coarse))
        return symbols

    def FineSelectionFunction(self, fine):
        symbols = []
        for i in self.__algorithms:
            symbols.extend(i.FineSelectionFunction(fine))
        return symbols

    def OnWarmupFinished(self):
        Singleton.Debug("OnWarmupFinished")

        if self.LiveMode:
            Singleton.Broker.ImportFromBroker()

            self.__initial_value = Singleton.Portfolio.TotalPortfolioValue
            self.Log(f"setting initial value to {self.__initial_value}")

        self.__cost = 0.0
        for i in self.__algorithms:
            # TypeError : unsupported operand type(s) for -=: 'Cash' and 'CashAmount'
            Singleton.Broker.Portfolio.Cash -= i.Portfolio.Cash
            for symbol, position in i.Portfolio.items():
                Singleton.Broker.Portfolio[symbol].Quantity -= position.Quantity

            cost = i.Allocation * self.__initial_value
            i.Portfolio.SetCash(cost)
            self.__cost += i.Portfolio.TotalPortfolioValue

        self.__initial_cost = self.__cost

        for i in self.__algorithms:
            i.OnWarmupFinished()

    def OnData(self, data):
        Singleton.Debug("OnData")
        for i in self.__algorithms:
            i.OnData(data)

    def OnDividend(self):
        Singleton.Debug("OnDividend")
        for i in self.__algorithms:
            i.OnDividend()

    def OnSecuritiesChanged(self, changes):
        Singleton.Debug(f"OnSecuritiesChanged {changes}")
        for i in self.__algorithms:
            # Only call if there's a relevant stock in i
            i.OnSecuritiesChanged(changes)

    def OnEndOfDay(self):
        Singleton.Debug("OnEndOfDay: {}".format(Singleton.Time))
        for i in self.__algorithms:
            i.OnEndOfDay()

        is_new_year = self.Time.year != self.__year
        if is_new_year:
            self.__year = self.Time.year

        is_new_month = self.Time.month != self.__month
        if is_new_month:
            self.__month = self.Time.month

        if self.__plot_orders and is_new_month:
            for i in self.__algorithms:
                self.Plot('Orders', i.Name, i.TotalOrders)

        if is_new_year:
            self.ResetOrders()
            if self.__reset:
                self.ResetPlot()

        if self.__plot_every_n_days_i % self.__plot_every_n_days == 0:
            if self._benchmark:
                self.Plot('Annual Saw Tooth Returns', self._benchmark.Name, self._benchmark.Performance)
                self.Plot('Strategy Equity', self._benchmark.Name, self._benchmark.Performance*self.__initial_cost)

            accum = 0.0
            pos = 0
            for i in self.__algorithms:
                accum += i.Portfolio.TotalPortfolioValue
                pos += 1
                self.Plot('Annual Saw Tooth Returns', i.Name, i.Performance)
                if self.__plot_value:
                    self.Plot("Value", i.Name, i.Portfolio.TotalPortfolioValue)
                if self.__plot_allocation:
                    self.Plot("Allocation", i.Name, round(100.0 * i.Allocation, 1))

        self.__plot_every_n_days_i += 1

        if self.__email_address:
            for i in self.__algorithms:
                if i.Email.HasContent:
                    i.Email.Send(f"{i.Name} (OnEndOfDay)")

    def GetTotalPortfolioValue(self):
        return sum([i.Portfolio.TotalPortfolioValue for i in self.__algorithms])

    def OnEndOfAlgorithm(self):
        for i in self.__algorithms:
            i.OnEndOfAlgorithm()
            i.Log(f"Total Orders: {i.TotalOrders}")
            i.Log(f"Performance: {i.Performance}")
            i.Log(f"Value: {i.Portfolio.TotalPortfolioValue}")

        if self.__email_address:
            for i in self.__algorithms:
                i.Email.Send(f"{i.Name} (Stopped)")

    def readjust_allocation(self):
        # total_value = self.GetTotalPortfolioValue()
        total_value = Singleton.Portfolio.TotalPortfolioValue
        for i in self.__algorithms:
            allocation = i.Portfolio.TotalPortfolioValue / total_value
            i.Allocation = math.floor(allocation * 100) / 100

    def OnBrokerageReconnect(self):
        __sync_cashbook()

    @accepts(self=object, order_event=OrderEvent)
    def OnOrderEvent(self, order_event):
        Singleton.Debug(f"> OnOrderEvent: {order_event}")
        Singleton.Broker.HandleOrderEvent(order_event)

class SimpleAlgorithm(object):
    def __init__(self, name="anonymous", allocation=None, initialize=True):
        self.Name = name
        self.Allocation = allocation
        if initialize:
            self.Initialize()

    def __getattr__(self, attr):
        """Delegate to parent."""
        if hasattr(Singleton, attr):
            return getattr(Singleton, attr)
        else:
            raise AttributeError(attr)

    @property
    def Performance(self):
        return 0.0

    ######################################################################
    def CoarseSelectionFunction(self, coarse): return []
    def FineSelectionFunction(self, fine): return []
    def OnWarmupFinished(self): pass
    def OnData(self, args): pass
    def OnDividend(self): pass
    def OnEndOfDay(self): pass
    def OnEndOfAlgorithm(self): pass
    def OnSecuritiesChanged(self, changes): pass
    def OnOrderEvent(self, order_event): pass
    def Initialize(self): self.Debug("Initialize call ignored")
    def SetCash(self, cash): self.Debug("SetCash call ignored")
    def SetStartDate(self, year, month, day): self.Debug("SetStartDate call ignored")
    def SetEndDate(self, year, month, day): self.Debug("SetEndDate call ignored")
    def SetWarmUp(self, period, resolution=Resolution.Daily): Singleton.SetWarmUpFromAlgorithm(period)
    def Log(self, message): Singleton.Log("[%s] %s" % (self.Name, message))
    def Debug(self, message): Singleton.Debug("[%s] %s" % (self.Name, message))
    def Error(self, message): Singleton.Error("[%s] %s" % (self.Name, message))

class Algorithm(SimpleAlgorithm):
    def __init__(self, name="anonymous", allocation=None, options={}):
        super().__init__(name=name, allocation=allocation, initialize=False)
        self.Options = options
        self.Portfolio = Portfolio(algorithm=self)
        self.Schedule = ScheduleWrapperManager(self)
        self.Email = Email()
        self.TotalOrders = 0
        self.Initialize()

    def post(self):
        self.Portfolio.ExecuteOrders()

    def __str__(self):
        return "[%s] %s" % (self.Name, str(self.Portfolio))

    def _tag(self, tag):
        return "%s: %s" % (self.Name, tag) if tag else self.Name

    @property
    def Performance(self):
        return round(self.Portfolio.Performance, 2)

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def Buy(self, symbol, quantity, tag=""):
        self.Debug("Buy(%s, %f)" % (symbol, quantity))
        return self.Portfolio.createOrder(symbol, quantity, OrderType.Market, tag=self._tag(tag))

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def Sell(self, symbol, quantity, tag=""):
        self.Debug("Sell(%s, %f)" % (symbol, quantity))
        return self.Portfolio.createOrder(symbol, -quantity, OrderType.Market, tag=self._tag(tag))

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def Order(self, symbol, quantity, tag=""):
        self.Debug("Order(%s, %f) [deprecated]" % (symbol, quantity))
        return self.MarketOrder(symbol, quantity, tag=tag)

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def MarketOrder(self, symbol, quantity, tag=""):
        self.Debug("MarketOrder(%s, %f)" % (symbol, quantity))
        return self.Portfolio.createOrder(symbol, quantity, OrderType.Market, tag=self._tag(tag))

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def LimitOrder(self, symbol, quantity, limit_price, tag=""):
        self.Debug("LimitOrder(%s, %f)" % (symbol, quantity))
        return self.Portfolio.createOrder(symbol, quantity, OrderType.Limit, limit_price=limit_price,
                                 tag=self._tag(tag))

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def StopMarketOrder(self, symbol, quantity, stop_price, tag=""):
        self.Debug("StopMarketOrder(%s, %f)" % (symbol, quantity))
        return self.Portfolio.createOrder(symbol, quantity, OrderType.StopMarket, stop_price=stop_price,
                                 tag=self._tag(tag))

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def StopLimitOrder(self, symbol, quantity, stop_price, limit_price, tag=""):
        self.Debug("StopLimitOrder(%s, %f)" % (symbol, quantity))
        return self.Portfolio.createOrder(symbol, quantity, OrderType.StopLimit, stop_price=stop_price,
                                 limit_price=limit_price, tag=self._tag(tag))

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def MarketOnOpenOrder(self, symbol, quantity, tag=""):
        self.Debug("MarketOnOpenOrder(%s, %f)" % (symbol, quantity))
        return self.Portfolio.createOrder(symbol, quantity, OrderType.MarketOnOpen, tag=self._tag(tag))

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def MarketOnCloseOrder(self, symbol, quantity, tag=""):
        self.Debug("MarketOnCloseOrder(%s, %f)" % (symbol, quantity))
        return self.Portfolio.createOrder(symbol, quantity, OrderType.MarketOnClose, tag=self._tag(tag))

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def OptionExerciseOrder(self, symbol, quantity, tag=""):
        self.Debug("OptionExerciseOrder(%s, %f)" % (symbol, quantity))
        return self.Portfolio.createOrder(symbol, quantity, OrderType.OptionExercise, tag=self._tag(tag))

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def Liquidate(self, symbol=None, tag=""):
        self.Debug("Liquidate(%s)" % symbol)
        self.Portfolio.liquidate(symbol=symbol, tag=self._tag(f"Liquidated {tag}"))
        self.Email.AppendKeyValue(symbol, "0%")

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def SetHoldings(self, symbol, percentage, liquidateExistingHoldings=False, tag=""):
        self.Debug("SetHoldings(%s, %f)" % (symbol, percentage))
        if liquidateExistingHoldings:
            to_liquidate = [s for s, p in iter(self.Portfolio.items()) if s != symbol and p.Quantity > 0]
            for s in to_liquidate:
                self.Liquidate(symbol=s, tag=self._tag(tag))

        percentage_str = f"{int(round(100.0*percentage, 0))}%"
        # percentage *= 0.999
        order = self._set_holdings_impl(symbol, percentage, tag=self._tag(f"{tag} ({percentage_str})"))
        self.Portfolio.AddOrder(order)
        self.Email.AppendKeyValue(symbol, percentage_str)

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def CalculateOrderQuantity(self, symbol, target):
        Singleton.readjust_allocation()
        global_current = Singleton.Portfolio[symbol].Quantity
        local_current = self.Portfolio[symbol].Quantity
        global_order = Singleton.CalculateOrderQuantity(symbol, self.Allocation * target)
        global_target = global_order + global_current
        local_order = global_target - local_current

        return local_order

    @accepts(self=object, symbol=Symbol, target=(int, float), tag=str)
    def _set_holdings_impl(self, symbol, target, tag=""):
        qty = self.CalculateOrderQuantity(symbol, target)

        # rounding off Order Quantity to the nearest multiple of Lot Size
        lot_size = Singleton.Securities[symbol].SymbolProperties.LotSize
        if lot_size < 1:
            lot_size = 0.001 # min order on Coinbase Pro
            # lot_size = min(1, 10 * lot_size) # prevent float limitations
            qty -= qty % lot_size

        # Calculate total unfilled quantity for open market orders
        order_ids = self.Broker.GetOrderIdsForPortfolio(self.Portfolio)
        open_orders = [Singleton.Transactions.GetOrderById(order_id) for order_id in order_ids]
        market_orders_quantity = sum([order.Quantity for order in open_orders
                                      if order.Symbol == symbol and order.Type in (OrderType.Market, OrderType.MarketOnOpen)])

        qty -= market_orders_quantity

        return InternalOrder(portfolio=self.Portfolio, symbol=symbol, quantity=qty, tag=tag)

    ######################################################################
    def CreateRollingWindow(self, symbol, window_size):
        rolling_window = RollingWindow[TradeBar](window_size)
        consolidator = TradeBarConsolidator(timedelta(1))
        consolidator.DataConsolidated += lambda _, bar: rolling_window.Add(bar)
        self.SubscriptionManager.AddConsolidator(symbol, consolidator)
        return rolling_window

class ScheduleWrapperManager(object):
    def __init__(self, algorithm):
        self._algorithm = algorithm
        self._func = None

    def On(self, date_rules, time_rules, func):
        self._func = ScheduleWrapper(func, self._algorithm.post)
        Singleton.Schedule.On(date_rules, time_rules, self._func.run)

class ScheduleWrapper(object):
    def __init__(self, func, post):
        self._func = func
        self._post = post

    def run(self):
        self._func()
        self._post()

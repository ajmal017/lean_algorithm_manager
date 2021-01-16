from datetime import date
from decorators import accepts


# pylint: disable=C0103,C0325,C0321,R0903,R0201,W0102,R0902,R0913,R0904,R0911

TradeBar = 0
RollingWindow = []

class TradeBarConsolidator(object):
    def __init__(self, _time_delta):
        self.DataConsolidated = []

class SubscriptionManager(object):
    def AddConsolidator(self, _symbol, _consolidator):
        pass

class Market(object):
    USA = 1
    GDAX = 2

class SecurityType(object):
    Equity = 1
    Crypto = 2

class Resolution(object):
    Daily = 1
    Minute = 2
    Second = 3

class SymbolProperties(object):
    @property
    def LotSize(self): return 1.0

class Settings(object):
    # @property
    # def DataSubscriptionLimit(self):  return int.MaxValue
    @property
    def LiquidateEnabled(self):  return True
    @property
    def FreePortfolioValue(self):  return 250
    @property
    def FreePortfolioValuePercentage(self):  return 0.0025
    # @property
    # def StalePriceTimeSpan(self):  return Time.OneHour
    # @property
    # def MaxAbsolutePortfolioTargetPercentage(self):  return 1000000000.0
    # @property
    # def MinAbsolutePortfolioTargetPercentage(self):  return 0.000000000

class Exchange(object):
    @property
    def ExchangeOpen(self): return True


class Symbol(object):
    @classmethod
    def Create(cls, ticker, security_type, market):
        return Symbol(ticker, security_type, market)

    def __init__(self, ticker, security_type=SecurityType.Equity, market=Market.USA):
        self.Value = ticker
        self.SecurityType = security_type
        self.Market = market

    def __hash__(self):
        return hash((self.Value, self.SecurityType, self.Market))

    def __eq__(self, other):
        return (self.Value, self.SecurityType, self.Market) == (other.Value, other.SecurityType, other.Market)

    def __ne__(self, other):
        return not(self == other)

    def __str__(self):
        return self.Value

    def __repr__(self):
        return self.__str__()


class Security(object):
    @accepts(self=object, ticker=(str, Symbol), price=(int, float))
    def __init__(self, ticker, price):
        self.Symbol = ticker if isinstance(ticker, Symbol) else Symbol(ticker)
        self.Price = float(price)
        self.Leverage = 1.0
        self.High = self.Price
        self.Low = self.Price
        self.Close = self.Price
        self.Open = self.Price
        self.Volume = 0.0
        self.SymbolProperties = SymbolProperties()

    @property
    def Exchange(self):
        return Exchange()


class InternalSecurityManager(dict):
    def __init__(self, securities=[]):
        super().__init__()
        for ticker, price in securities:
            self[ticker] = Security(ticker, price)

    @accepts(self=object, key=(Symbol, str), value=Security)
    def __setitem__(self, key, value):
        if isinstance(key, str):
            key = self.CreateSymbol(key)
        return super().__setitem__(key, value)

    @accepts(self=object, key=(Symbol, str))
    def __getitem__(self, key):
        if isinstance(key, str):
            key = self.CreateSymbol(key)
        if key not in self:
            return self.NoValue(key)
        return super().__getitem__(key)

    def CreateSymbol(self, key):
        return Symbol.Create(key, SecurityType.Equity, Market.USA)

    def NoValue(self, key):
        raise KeyError("Could not find key \"{}\"".format(key))


class BrokerageName(object):
    Default = 0
    InteractiveBrokersBrokerage = 1


class OrderDuration(object):
    GTC = 0
    Day = 1

class OrderDirection(object):
    Buy = 1
    Hold = 0
    Sell = -1

# lean/Common/Orders/OrderTypes.cs
class OrderType(object):
    Market = 1
    Limit = 2
    StopMarket = 3
    StopLimit = 4
    MarketOnOpen = 5
    MarketOnClose = 6
    OptionExercise = 7

    @classmethod
    def TypeToString(cls, order_type):
        if order_type is OrderType.Market: return "Market"
        elif order_type is OrderType.Limit: return "Limit"
        elif order_type is OrderType.StopMarket: return "StopMarket"
        elif order_type is OrderType.StopLimit: return "StopLimit"
        elif order_type is OrderType.MarketOnOpen: return "MarketOnOpen"
        elif order_type is OrderType.MarketOnClose: return "MarketOnClose"
        elif order_type is OrderType.OptionExercise: return "OptionExercise"

class OrderStatus(object):
    New = 0,
    Submitted = 1
    PartiallyFilled = 2
    Filled = 3
    Canceled = 5
    # None = 6
    Invalid = 7
    CancelPending = 8
    UpdateSubmitted = 9

class Order(object):
    def __init__(self, order_id, symbol, quantity, order_type=OrderType.Market,
                 status=OrderStatus.New, tag=""):
        self.Id = order_id
        self.Symbol = symbol
        self.Price = 0
        self.Quantity = quantity
        self.Type = order_type
        self.Status = status
        self.Duration = OrderDuration.GTC
        self.Tag = tag
        self.AverageFillPrice = None
        self.QuantityFilled = None
        self.Value = 0

    def ToString(self):
        return f"Order({self.Id}, {self.Status}, {OrderType.TypeToString(self.Type)}, {self.Symbol}, {self.Quantity})"

    def __str__(self):
        return self.ToString()

    def __repr__(self):
        return self.__str__()

# lean/Common/Orders/OrderTicket.cs
class OrderTicket(object):
    @accepts(self=object, order_id=int, symbol=Symbol,
             quantity=(int, float), order_type=int, status=int, tag=str)
    def __init__(self, order_id, symbol, quantity, order_type=OrderType.Market,
                 status=OrderStatus.New, tag=""):
        self.Order = Order(order_id, symbol, quantity, order_type, status, tag)
        self.SecurityType = symbol.SecurityType
        self.OrderEvents = []

    @property
    def OrderId(self):
        return self.Order.Id

    @property
    def Status(self):
        return self.Order.Status

    @Status.setter
    def Status(self, value):
        self.Order.Status = value

    @property
    def Symbol(self):
        return self.Order.Symbol

    @property
    def Quantity(self):
        return self.Order.Quantity

    @property
    def OrderType(self):
        return self.Order.Type

    @property
    def AverageFillPrice(self):
        return sum([event.FillPrice for event in self.OrderEvents]) / self.QuantityFilled

    @property
    def QuantityFilled(self):
        return sum([event.FillQuantity for event in self.OrderEvents])

    def ToString(self):
        return "Ticket(%s, %.1f, %s)" % (self.Symbol, self.Quantity, self.OrderType)

    def __str__(self):
        return self.ToString()

    def __repr__(self):
        return self.__str__()

    def Cancel(self, tag=""):
        pass


# class Amount(float):
#     def __init__(self, amount):
#         self.amount = amount

#     @property
#     def Amount(self):
#         return self.amount

#     def __float__(self):
#          return float(self.amount)

#     def __eq__(self, other):
#         return float(self) == float(other)

# class Value(object):
#     def __init__(self, amount):
#         self.value = Amount(amount)

#     @property
#     def Value(self):
#         return self.value


class CashAmount(float):
    @property
    def Amount(self):
        return self

class OrderFee(object):
    def __init__(self, value):
        self.Value = CashAmount(value)

class OrderEvent(object):
    def __init__(self, order_id, symbol, quantity, price=None, status=OrderStatus.New):
        self.OrderId = order_id
        self.Symbol = symbol
        self.Quantity = quantity
        self.Status = status
        self.OrderFee = OrderFee(0.0)
        self.FillPrice = 0.0
        self.FillQuantity = 0.0
        if price:
            self.FillPrice = price
        if status == OrderStatus.Filled:
            self.FillQuantity = quantity
        if status == OrderStatus.PartiallyFilled:
            self.FillQuantity = quantity / 2.0

    def __str__(self):
        return f"OrderEvent({self.OrderId}, {self.Status}, {self.Symbol}, {self.Quantity})"


class SecurityTransactionManager(dict):
    __last_order_id = 0

    def GetOrderById(self, order_id):
        # TODO: should return the Order
        return self.GetOrderTicket(order_id)

    def GetOrderTicket(self, order_id):
        return self[order_id]

    # @accepts(self=object, order=InternalOrder)
    def AddOrder(self, symbol, quantity, order_type=OrderType.Market, status=OrderStatus.New):
        return OrderTicket(self.GetIncrementOrderId, symbol, quantity, order_type=order_type, status=status)

    @property
    def GetIncrementOrderId(self):
        SecurityTransactionManager.__last_order_id += 1
        return SecurityTransactionManager.__last_order_id

    def CancelOrder(self, order_id, tag=""):
        return self.RemoveOrder(order_id, tag)

    def RemoveOrder(self, order_id, tag=""):
        pass

    def CancelOpenOrders(self, symbol):
        # return List<OrderTicket>
        pass

    def GetOpenOrders(self):
        # return List<Order>
        pass

    def GetSufficientCapitalForOrder(self, _SecurityPortfolioManager, _Order):
        return True


class CashAmount(float):
    @property
    def Amount(self):
        return self


class Cash(CashAmount):
    def __new__(cls, currency_symbol, amount, price=1.0):
        return super().__new__(cls, amount)

    def __init__(self, currency_symbol, amount, price=1.0):
        CashAmount.__init__(amount)
        self.CurrencySymbol = currency_symbol
        self.ConversionRate = price


class CashBook(dict):
    @property
    def Keys(self):
        return self.keys()



class SecurityPortfolioManager(dict):
    def __init__(self):
        self.Securities = InternalSecurityManager()
        self.Transactions = SecurityTransactionManager()
        self.Cash = Cash('USD', 0.0, 1.0)
        self.CashBook = CashBook()
        self.CashBook['USD'] = Cash('USD', 0.0, 1.0)

class Time:
    TODAY = date(1, 1, 1)
    @classmethod
    def date(cls):
        return Time.TODAY

# Dummy interface.
class QCAlgorithm(object):
    def __init__(self, default_order_status=OrderStatus.Submitted):
        self.Portfolio = SecurityPortfolioManager()
        self.Securities = self.Portfolio.Securities
        self.Transactions = self.Portfolio.Transactions
        self.LiveMode = False
        self.IsWarmingUp = False
        self.SetBrokerageModel = BrokerageName.Default
        self.Time = Time
        self._default_order_status = default_order_status
        self._algorithms = []
        self._benchmarks = []
        self._warm_up = None
        self._warm_up_from_algorithm = False
        self.Initialize()

    def Initialize(self): pass
    def OnWarmupFinished(self): pass
    def SetCash(self, cash): pass
    def SetStartDate(self, year, month, day): pass
    def SetEndDate(self, year, month, day): pass
    def SetWarmUp(self, period): pass
    def OnOrderEvent(self, order_event): pass
    def Log(self, message): print(message)
    def Debug(self, message): print(message)
    def Error(self, message): print(message)
    def AddChart(self, plot): pass
    def Plot(self, chart_name, series_name, value): pass

    def AddSecurity(self, _security_type, ticker, _resolution):
        return self.Securities[ticker]

    def AddEquity(self, ticker, _resolution):
        return self.AddSecurity(None, ticker, None)

    def AddCrypto(self, ticker, resolution):
        return self.AddSecurity(None, ticker, None)

    def _mockOrder(self, symbol, quantity, order_type):
        ticket = self.Transactions.AddOrder(symbol, quantity, order_type=order_type,
                                            status=self._default_order_status)
        ticket.Status = OrderStatus.Submitted
        self.Transactions[ticket.OrderId] = ticket
        return ticket

    def MarketOrder(self, symbol, quantity, _asynchronous, _tag):
        return self._mockOrder(symbol, quantity, OrderType.Market)

    def LimitOrder(self, symbol, quantity, _limit_price, _tag):
        return self._mockOrder(symbol, quantity, OrderType.Limit)

    def StopMarketOrder(self, symbol, quantity, _stop_price, _tag):
        return self._mockOrder(symbol, quantity, OrderType.StopMarket)

    def StopLimitOrder(self, symbol, quantity, _stop_price, _limit_price, _tag):
        return self._mockOrder(symbol, quantity, OrderType.StopLimit)

    def MarketOnOpenOrder(self, symbol, quantity, _tag):
        return self._mockOrder(symbol, quantity, OrderType.MarketOnOpen)

    def MarketOnCloseOrder(self, symbol, quantity, _tag):
        return self._mockOrder(symbol, quantity, OrderType.MarketOnClose)

    def OptionExerciseOrder(self, symbol, quantity, _tag):
        return self._mockOrder(symbol, quantity, OrderType.OptionExercise)

    def SetHoldings(self, symbol, percentage, liquidateExistingHoldings=False, tag=""):
        pass

    def Liquidate(self, symbol=None, tag=""):
        pass

    def CalculateOrderQuantity(self, symbol, target):
        return 1

class SeriesType(object):
    Line = 1
    Scatter = 2
    Candle = 3
    Bar = 4
    Flag = 5

class Series(object):
    def __init__(self, chart, series, seriesType, unit): pass

class Chart(object):
    def __init__(self, name): pass
    def AddSeries(self, series): pass

"""
MD5: acfb3f8e6f320742ca005a8868aeb86b
"""

from decimal import Decimal
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

class SecurityType(object):
    Equity = 1

class Resolution(object):
    Daily = 1
    Minute = 2
    Second = 3

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


class SymbolProperties(object):
    @property
    def LotSize(self):
        return Decimal(1)

class Security(object):
    @accepts(self=object, ticker=(str, Symbol), price=(float, int))
    def __init__(self, ticker, price):
        self.Symbol = ticker if isinstance(ticker, Symbol) else Symbol(ticker)
        self.Price = Decimal(price)
        self.Leverage = 1.0
        self.High = self.Price
        self.Low = self.Price
        self.Close = self.Price
        self.Open = self.Price
        self.Volume = 0.0
        self.SymbolProperties = SymbolProperties()


class InternalSecurityManager(dict):
    def __init__(self, securities=[]):
        super(InternalSecurityManager, self).__init__()
        for ticker, price in securities:
            self[ticker] = Security(ticker, price)

    @accepts(self=object, key=(Symbol, str), value=Security)
    def __setitem__(self, key, value):
        if isinstance(key, str):
            key = self.createKey(key)
        return super(InternalSecurityManager, self).__setitem__(key, value)

    @accepts(self=object, key=(Symbol, str))
    def __getitem__(self, key):
        if isinstance(key, str):
            key = self.createKey(key)
        if key not in self:
            return self.NoValue(key)
        return super(InternalSecurityManager, self).__getitem__(key)

    def createKey(self, key):
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
        self.AbsoluteQuantity = 0
        self.Value = 0

    def ToString(self):
        return "OrderId: {0} {1} {2} order for {3} units of {5}" \
            .format(self.Id, self.Status, OrderType.TypeToString(self.Type), self.Quantity, self.Symbol)

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
        return sum([event.FillPrice for event in self.OrderEvents]) / float(self.QuantityFilled)

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

class OrderEvent(object):
    def __init__(self, order_id, symbol, quantity, price=None, status=OrderStatus.New):
        self.OrderId = order_id
        self.Symbol = symbol
        self.Quantity = quantity
        self.Status = status
        self.OrderFee = 0
        self.FillPrice = 0
        self.FillQuantity = 0
        if price:
            self.FillPrice = price
        if status == OrderStatus.Filled:
            self.FillQuantity = quantity
        if status == OrderStatus.PartiallyFilled:
            self.FillQuantity = quantity / 2

    def __str__(self):
        return "OrderId: %d Submitted order for %d units of %s" % \
            (self.OrderId, self.Quantity, self.Symbol)


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


# Dummy interface.
class QCAlgorithm(object):
    def __init__(self, default_order_status=OrderStatus.Submitted):
        self.Securities = InternalSecurityManager()
        self.Portfolio = None
        self.Transactions = SecurityTransactionManager()
        self.LiveMode = False
        self.IsWarmingUp = False
        self._default_order_status = default_order_status
        self._algorithms = []
        self.SetBrokerageModel = BrokerageName.Default
        self.Time = ""
        self._warm_up = None
        self._warm_up_from_algorithm = False
        self.Initialize()

    def Initialize(self): pass
    def SetCash(self, *args, **kwargs): pass
    def SetStartDate(self, year, month, day): pass
    def SetEndDate(self, year, month, day): pass
    def SetWarmUp(self, period): pass
    def OnOrderEvent(self, order_event): pass
    def Log(self, message): print(message)
    def Debug(self, message): print(message)
    def Error(self, message): print(message)
    def AddChart(self, plot): pass
    def Plot(self, chart_name, series_name, value): pass


    def AddEquity(self, ticker, _resolution):
        return self.Securities[ticker]

    def _mockOrder(self, symbol, quantity, order_type):
        ticket = self.Transactions.AddOrder(symbol, quantity, order_type=order_type,
                                            status=self._default_order_status)
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


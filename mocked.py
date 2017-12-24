"""
MD5: a31e1f00c11da8ef0010e57d00540e41
"""
from decimal import Decimal
from types import NoneType  # pylint: disable=W0611


# pylint: disable=C0103,C0325,C0321,R0903,R0201,W0102,R0902,R0913,R0904,R0911
def accepts(**types):
    def check_accepts(f):
        assert len(types) == f.func_code.co_argcount, \
            'wrong number of arguments in "%s"' % f.func_name

        def new_f(*args, **kwds):
            for i, v in enumerate(args):
                if types.has_key(f.func_code.co_varnames[i]) and \
                        not isinstance(v, types[f.func_code.co_varnames[i]]):
                    raise Exception("arg '%s'=%r does not match %s" %
                                    (f.func_code.co_varnames[i], v, types[f.func_code.co_varnames[i]]))
                    # del types[f.func_code.co_varnames[i]]

            for k, v in kwds.iteritems():
                if types.has_key(k) and not isinstance(v, types[k]):
                    raise Exception("arg '%s'=%r does not match %s" %
                                    (k, v, types[k]))

            return f(*args, **kwds)
        new_f.func_name = f.func_name
        return new_f
    return check_accepts


class Market(object):
    USA = 1

class SecurityType(object):
    Equity = 1

class Resolution(object):
    Daily = 1
    Minute = 2
    Second = 3


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

# lean/Common/Orders/OrderTicket.cs
class OrderTicket(object):
    __last_order_id = 0

    def __init__(self, symbol, quantity, price=None, order_type=OrderType.Market,
                 status=OrderStatus.New):
        OrderTicket.__last_order_id += 1
        self.Symbol = symbol
        self.Quantity = quantity
        self.Type = order_type
        self.Status = status
        self.FillQuantity = 0
        self.FillPrice = 0
        self.OrderId = OrderTicket.__last_order_id
        self.OrderFee = 0
        if price:
            self.FillPrice = price
        if status == OrderStatus.Filled:
            self.FillQuantity = quantity
        if status == OrderStatus.PartiallyFilled:
            self.FillQuantity = quantity / 2

    def __str__(self):
        return "OrderId: %d Submitted %s order for %d units of %s" % \
            (self.OrderId, OrderType.TypeToString(self.Type), self.Quantity, self.Symbol)


class Transactions(dict):
    def GetOrderById(self, order_id):
        return self[order_id]


class Symbol(object):

    @classmethod
    def Create(cls, ticker, security_type, market):
        return Symbol(ticker, security_type, market)

    def __init__(self, ticker="", security_type=SecurityType.Equity, market=Market.USA):
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


class Security(object):
    def __init__(self, ticker, **kwargs):
        self.Symbol = Symbol(ticker)
        self.Price = Decimal(kwargs['price'] if 'price' in kwargs else 0.0)

class Securities(dict):
    def __init__(self, securities=[]):
        super(Securities, self).__init__()
        for sec in securities:
            symbol = sec[0]
            ticker = symbol.Value
            price = Decimal(sec[1])
            self[ticker] = Security(symbol, price=price)


class BrokerageName(object):
    Default = 0
    InteractiveBrokersBrokerage = 1


# Dummy interface.
class QCAlgorithm(object):
    def __init__(self, default_order_status=OrderStatus.Submitted):
        self.Securities = Securities()
        self.Portfolio = None
        self.Transactions = Transactions()
        self.LiveMode = False
        self.Time = ''
        self.IsWarmingUp = False
        self._default_order_status = default_order_status
        self._broker = None
        self._algorithms = []
        self._warm_up_period = 0
        self.SetBrokerageModel = BrokerageName.Default
        self.Initialize()

    def Initialize(self): pass
    def SetCash(self, *args, **kwargs): pass
    def SetStartDate(self, *args, **kwargs): pass
    def SetEndDate(self, *args, **kwargs): pass
    def SetWarmUp(self, period): pass
    def OnOrderEvent(self, event_order): pass
    def Log(self, message): print(message)
    def Debug(self, message): print(message)
    def Error(self, message): print(message)
    def AddChart(self, plot): pass
    def Plot(self, chart_name, series_name, value): pass


    def AddEquity(self, ticker, _resolution):
        return Security(ticker)

    # To be used in tests
    def SetDefaultOrderStatus(self, status):
        self._default_order_status = status

    def SetOrderStatus(self, status, order=None, quantity=None):
        if order is None:
            for o in self._broker.submitted.values():
                self.SetOrderStatus(status, order=o)
            return

        ticket = self.Transactions[order.Ticket.OrderId]
        ticket.Status = status
        if quantity:
            ticket.FillQuantity = quantity
        else:
            ticket.FillQuantity = order.Quantity
        ticket.FillPrice = self.Securities[ticket.Symbol.Value].Price
        self.OnOrderEvent(ticket)


    def _mockOrder(self, symbol, quantity, order_type):
        ticket = OrderTicket(symbol, quantity, order_type=order_type, status=self._default_order_status)
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

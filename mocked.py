"""
MD5: ea0e21d0723155900521cd57f4f22eb8
"""
from decimal import Decimal

# pylint: disable=C0103,C0325,C0321,R0903,R0201,W0102
class SecurityType(object):
    Equity = 1

class Resolution(object):
    Daily = 1
    Minute = 2
    Second = 3

class OrderType(object):
    Market = 1
    Limit = 2
    StopMarket = 3
    StopLimit = 4
    MarketOnOpen = 5
    MarketOnClose = 6

# lean/Common/Orders/OrderTypes.cs
class OrderStatus(object):
    New = 0,
    Submitted = 1
    PartiallyFilled = 2
    Filled = 3
    Canceled = 5
    # None = 6
    Invalid = 7
    CancelPending = 8

class OrderTicket(object):
    def __init__(self, symbol, quantity, order_type=OrderType.Market,
                 status=OrderStatus.New):
        self.Symbol = symbol
        self.Quantity = quantity
        self.Type = order_type
        self.Status = status
        self.FillQuantity = 0
        if status in [OrderStatus.Filled, OrderStatus.PartiallyFilled]:
            self.FillPrice = 1.2345
            self.FillQuantity = quantity
            if status == OrderStatus.PartiallyFilled:
                self.FillQuantity = quantity / 2

    def ToString(self):
        print('TICKET [%s] x %f' %(self.Symbol, self.Quantity))


class Symbol(object):
    def __init__(self, ticker, **_kwargs):
        self.Value = ticker
        self.SecurityType = SecurityType.Equity

    def __hash__(self):
        return hash((self.Value, self.SecurityType))

    def __eq__(self, other):
        return (self.Value, self.SecurityType) == (other.Value, other.SecurityType)

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
            symb = sec[0]
            price = Decimal(sec[1])
            self[symb] = Security(symb, price=price)

# Dummy interface.
class QCAlgorithm(object):
    def __init__(self):
        self.Securities = Securities()
        self.Portfolio = None
        self.Initialize()
        self.Transactions = None
        self.LiveMode = False
        self.Time = ''

    def AddEquity(self, ticker, _resolution): return Security(ticker)
    def Initialize(self): pass
    def SetCash(self, *args, **kwargs): pass
    def SetStartDate(self, *args, **kwargs): pass
    def SetEndDate(self, *args, **kwargs): pass
    def Log(self, args): print(args)
    def Debug(self, args): self.Log(args)

    def MarketOrder(self, symbol, quantity, _asynchronous, _tag):
        return OrderTicket(symbol, quantity, order_type=OrderType.Market, status=OrderStatus.Filled)

    def LimitOrder(self, symbol, quantity, _limit_price, _tag):
        return OrderTicket(symbol, quantity, order_type=OrderType.Limit, status=OrderStatus.Submitted)

    def StopMarketOrder(self, symbol, quantity, _stop_price, _tag):
        return OrderTicket(symbol, quantity, order_type=OrderType.StopMarket, status=OrderStatus.Submitted)

    def StopLimitOrder(self, symbol, quantity, _stop_price, _limit_price, _tag):
        return OrderTicket(symbol, quantity, order_type=OrderType.StopLimit, status=OrderStatus.Submitted)

    def SetWarmUp(self, period): pass

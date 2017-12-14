"""
MD5: 08f9e4fc084a1643e22ec4d8ac5eb607
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
    __last_order_id = 0

    def __init__(self, symbol, quantity, price=None, order_type=OrderType.Market,
                 status=OrderStatus.New):
        self.Symbol = symbol
        self.Quantity = quantity
        self.Type = order_type
        self.Status = status
        self.FillQuantity = 0
        self.FillPrice = 0
        OrderTicket.__last_order_id += 1
        self.OrderId = OrderTicket.__last_order_id
        if price:
            self.FillPrice = price
        if status == OrderStatus.Filled:
            self.FillQuantity = quantity
        if status == OrderStatus.PartiallyFilled:
            self.FillQuantity = quantity / 2

    def ToString(self):
        print('TICKET [%s] x %f' %(self.Symbol, self.Quantity))


class Transactions(dict):
    def __init__(self):
        super(Transactions, self).__init__()

    def GetOrderById(self, order_id):
        return self[order_id]


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
    def __init__(self, default_order_status=OrderStatus.Submitted):
        self.Securities = Securities()
        self.Portfolio = None
        self.Transactions = Transactions()
        self.LiveMode = False
        self.Time = ''
        self.IsWarmingUp = False
        self.WarmUp = 0
        self.__default_order_status = default_order_status
        self._broker = None
        self._algorithms = []
        self.Initialize()

    def Initialize(self): pass
    def SetCash(self, *args, **kwargs): pass
    def SetStartDate(self, *args, **kwargs): pass
    def SetEndDate(self, *args, **kwargs): pass
    def SetWarmUp(self, period): pass
    def OnOrderEvent(self, event_order): pass
    def Log(self, args): print(args)
    def Debug(self, args): self.Log(args)

    def AddEquity(self, ticker, _resolution):
        return Security(ticker)

    # To be used in tests
    def SetDefaultOrderStatus(self, status):
        self.__default_order_status = status

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
        ticket.FillPrice = self.Securities[ticket.Symbol].Price
        self.OnOrderEvent(ticket)


    def MarketOrder(self, symbol, quantity, _asynchronous, _tag):
        ticket = OrderTicket(symbol, quantity, order_type=OrderType.Market,
                             status=self.__default_order_status)
        self.Transactions[ticket.OrderId] = ticket
        return ticket

    def LimitOrder(self, symbol, quantity, _limit_price, _tag):
        ticket = OrderTicket(symbol, quantity, order_type=OrderType.Limit,
                             status=self.__default_order_status)
        self.Transactions[ticket.OrderId] = ticket
        return ticket

    def StopMarketOrder(self, symbol, quantity, _stop_price, _tag):
        ticket = OrderTicket(symbol, quantity, order_type=OrderType.StopMarket,
                             status=self.__default_order_status)
        self.Transactions[ticket.OrderId] = ticket
        return ticket

    def StopLimitOrder(self, symbol, quantity, _stop_price, _limit_price, _tag):
        ticket = OrderTicket(symbol, quantity, order_type=OrderType.StopLimit,
                             status=self.__default_order_status)
        self.Transactions[ticket.OrderId] = ticket
        return ticket

    def SetWarmUp(self, period): pass

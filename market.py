"""
MD5: a1542f0bdfe75aa0300683c1fb1a7076
"""

# pylint: disable=C0321,W0401,W0614
try: QCAlgorithm
except NameError: from mocked import *

from decimal import Decimal
from decorators import accepts
from algorithm_manager import Singleton

# pylint: disable=C0111,C0103,C0112,E1136,R0903,R0913,R0914,R0902,R0911

class ISymbolDict(dict):
    @accepts(self=object, key=(Symbol, str), value=object)
    def __setitem__(self, key, value):
        key = ISymbolDict.createKey(key)
        return super().__setitem__(key, value)

    def __str__(self):
        items = []
        for k, v in iter(super().items()):
            items.append('{}: {}; '.format(k, v))
        return '{ ' + ', '.join(items) + ' }'

    @accepts(self=object, key=(Symbol, str))
    def __getitem__(self, key):
        key = ISymbolDict.createKey(key)
        if key not in self:
            return self.NoValue(key)
        return super().__getitem__(key)

    @classmethod
    def createKey(cls, key):
        if isinstance(key, Symbol):
            return key
        elif isinstance(key, str):
            try:
                return Singleton.QCAlgorithm.Securities[key].Symbol
            except KeyError:
                return key
            # return Symbol.Create(key, SecurityType.Equity, Market.USA)
        else:
            raise TypeError("Expected str or Symbol, but got {}".format(key))

    def NoValue(self, key):
        raise KeyError("Could not find key \"{}\"".format(key))


class InternalSecurity(object):
    '''Security'''
    @accepts(self=object, security=Security)
    def __init__(self, security):
        self._internal = security
        self.Holdings = None

    def __getattr__(self, attr):
        """Delegate to parent."""
        if hasattr(self._internal, attr):
            return getattr(self._internal, attr)
        else:
            raise AttributeError(attr)

    def SetHoldings(self, position):
        self.Holdings = position
        raise NotImplementedError("Did not implement SetHoldings")

    @property
    def HoldStock(self):
        return self.Holdings.HoldStock

    @property
    def Invested(self):
        return self.HoldStock


class Securities(ISymbolDict):
    '''InternalSecurityManager'''
    @accepts(self=object, key=(Symbol, str), value=InternalSecurity)
    def __setitem__(self, key, value):
        return super().__setitem__(key, value)

    @accepts(self=object, security=Security)
    def Add(self, security):
        Singleton.Log("Securities.Add({})".format(type(security)))
        if security.Symbol not in self:
            self[security.Symbol] = InternalSecurity(security)


class Position(object):
    '''SecurityHolding'''

    def __init__(self, symbol, quantity, price_per_share):
        self.Symbol = symbol
        self.Quantity = float(quantity)
        self.AveragePrice = float(price_per_share)
        self.TotalSaleVolume = 0.0
        self.Profit = 0.0
        self.LastTradeProfit = 0.0
        self.TotalFees = 0.0
        self.Security = None

    def __str__(self):
        return "symbol: %s, qty: %.1f, cost: $%.2f" % (self.Symbol, self.Quantity, self.HoldingsCost())

    def __repr__(self):
        return self.__str__()

    def HoldingsCost(self):
        return self.Quantity * self.AveragePrice

    @property
    def AbsoluteQuantity(self):
        return int(self.Quantity)

    @property
    def HoldStock(self):
        return self.AbsoluteQuantity > 0

    @property
    def Invested(self):
        return self.HoldStock

    @property
    def NetProfit(self):
        return self.Profit - self.TotalFees

    @property
    def Price(self):
        return self.Security.Price

    def Fill(self, quantity, price_per_share=None):
        if quantity == 0:
            return
        elif quantity < 0:
            price_per_share = self.AveragePrice

        denominator = self.Quantity + quantity
        if denominator == 0:
            self.AveragePrice = 0
            self.Quantity = 0
            return
        old_sum = self.Quantity * self.AveragePrice
        new_sum = (old_sum + quantity * price_per_share)
        self.AveragePrice = new_sum / denominator
        self.Quantity += quantity


class Portfolio(ISymbolDict):
    '''SecurityPortfolioManager'''
    def __init__(self, broker, cash=0.0):
        super().__init__()
        self._initial_value = float(cash)
        self.Broker = broker
        self.Securities = Securities()
        self.CashBook = float(cash)
        self.UnsettledCashBook = 0.0
        self.Log = Singleton.Log
        self.Debug = Singleton.Debug
        self.Error = Singleton.Error

    def SetupLog(self, algorithm):
        self.Log = algorithm.Log
        self.Debug = algorithm.Debug
        self.Error = algorithm.Error

    def NoValue(self, key):
        return Position(key, 0, 0.0)

    @property
    def Transactions(self):
        raise NotImplementedError("Did not implement Transactions")
        # return Singleton.QCAlgorithm.Transactions

    @property
    def HoldStock(self):
        return self.TotalHoldingsValue > 0.0

    @property
    def Invested(self):
        return self.HoldStock

    @property
    def Keys(self):
        return self.keys()

    @property
    def TotalPortfolioValue(self):
        return self.TotalHoldingsValue + self.CashBook - self.TotalFees

    @property
    def TotalHoldingsValue(self):
        return sum([pos.Quantity * float(Singleton.QCAlgorithm.Securities[symb].Price)
                    for symb, pos in iter(self.items())])

    @property
    def TotalHoldingsCost(self):
        return sum([pos.Quantity * pos.AveragePrice for _symb, pos in iter(self.items())])

    @property
    def UnrealizedProfit(self):
        return self.TotalHoldingsValue - self.TotalHoldingsCost

    @property
    def Performance(self):
        return 100.0 * ((self.TotalPortfolioValue / self._initial_value) - 1.0)

    @property
    def TotalProfit(self):
        return sum([pos.Profit for pos in self.values()])

    @property
    def TotalFees(self):
        return sum([pos.TotalFees for pos in self.values()])

    def __str__(self):
        return 'Portfolio([' + '), ('.join(map(str, self.values())) + '])'

    def __repr__(self):
        return self.__str__()

    # @accepts(self=object, order_event=OrderEvent, order=object)
    def ProcessOrderEvent(self, order_event, order):
        if order_event.Status == OrderStatus.Invalid:
            self.Debug("INVALID: {0}".format(order_event))

        elif order_event.Status in [OrderStatus.Filled, OrderStatus.PartiallyFilled]:
            prefix = "PARTIALLY " if order_event.Status == OrderStatus.PartiallyFilled else ""
            self.Debug("{0}FILLED: {1} at FILL PRICE: {2}".format(prefix, order_event, order_event.FillPrice))
            self.Debug("Before: {}".format(self[order.Symbol].Quantity))
            self.FillOrder(order.Symbol, float(order_event.FillQuantity),
                           float(order_event.FillPrice), float(order_event.OrderFee.Value.Amount))
            self.Debug("After: {}".format(self[order.Symbol].Quantity))

        else:
            self.Debug("????: {0} at FILL PRICE: {1}".format(order_event, order_event.FillPrice))


    # @accepts(self=object, symbol=Symbol, quantity=(int, float), price_per_share=(float), fees=(float))
    def FillOrder(self, symbol, quantity, price_per_share, fees=0.0):
        """Used by Broker."""
        if symbol not in self:
            self[symbol] = Position(symbol, quantity, price_per_share)
        else:
            self[symbol].Fill(quantity, price_per_share)

        self.CashBook -= quantity * price_per_share
        self[symbol].TotalFees += fees

        remaining_quantity = self[symbol].Quantity
        if remaining_quantity < 0:
            message = "InternalOrder removed too many positions of %s" % symbol
            self.Debug("EXCEPTION: %s" % message)
            raise Exception(message)
        elif remaining_quantity == 0:
            self.pop(symbol)

    # @accepts(self=object, order=InternalOrder)
    def AddOrder(self, order):
        self.Debug("Adding Order {}".format(order))
        if order.Quantity == 0:
            self.Debug("Warning: Avoiding submitting order that has zero quantity.")
            return
        self.Broker.AddOrder(order)
        self.Debug("Added Order")


    @accepts(self=object, symbol=(Symbol, None), tag=str)
    def Liquidate(self, symbol=None, tag=""):
        if not symbol:
            symbols = [sym for sym, pos in iter(self.items()) if pos.Quantity > 0]
            for s in symbols:
                self.Debug("self.Liquidate({})".format(s))
                self.Liquidate(symbol=s, tag=tag)
        else:
            self.Debug("InternalOrder({}, {})".format(symbol, -self[symbol].Quantity))
            order = InternalOrder(portfolio=self, symbol=symbol, quantity=-self[symbol].Quantity, tag=tag)
            self.AddOrder(order)

    @accepts(self=object, symbol=Symbol, target_alloc=float, tag=str)
    def GenerateOrder(self, symbol, target_alloc, tag=""):
        need_to_buy_qty = self.CalculateOrderQuantity(symbol, target_alloc)
        return InternalOrder(portfolio=self, symbol=symbol, quantity=need_to_buy_qty, tag=tag)

    @accepts(self=object, symbol=Symbol, percentage=float)
    def CalculateOrderQuantity(self, symbol, target):
        security = Singleton.QCAlgorithm.Securities[symbol]
        unit_price = float(security.Price)
        old_qty = self[symbol].Quantity

        # can't order it if we don't have data
        if unit_price == 0.0:
            return 0

        # if targeting zero, simply return the negative of the quantity
        if target == 0.0:
            return -old_qty

        # this is the value in dollars that we want our holdings to have
        targetPortfolioValue = target * (self.TotalHoldingsValue + self.CashBook)
        currentHoldingsValue = self[symbol].Quantity * unit_price

        # remove directionality, we'll work in the land of absolutes
        targetOrderValue = abs(targetPortfolioValue - currentHoldingsValue)
        direction = OrderDirection.Buy if targetPortfolioValue > currentHoldingsValue else OrderDirection.Sell

        # calculate the total margin available
        # security = Securities[symbol]
        # return security.MarginModel.GetMarginRemaining(this, security, direction)
        # marginRemaining = self.Portfolio.GetMarginRemaining(symbol, direction)
        # if marginRemaining <= 0:
        #     return 0

        # continue iterating while we do not have enough margin for the order
        # marginRequired = 0.0
        orderValue = 0.0
        orderFees = 0.0
        feeToPriceRatio = 0.0

        # compute the initial order quantity
        orderQuantity = targetOrderValue / unit_price

        # rounding off Order Quantity to the nearest multiple of Lot Size
        lot_size = float(security.SymbolProperties.LotSize)
        orderQuantity -= orderQuantity % lot_size

        while True:
            # reduce order quantity by feeToPriceRatio, since it is faster than by lot size
            # if it becomes nonpositive, return zero
            orderQuantity -= feeToPriceRatio
            if orderQuantity <= 0:
                return 0

            # generate the order
            # order = self._parent.MarketOrder(security.Symbol, orderQuantity, self.UtcTime)
            # orderValue = order.GetValue(security)
            orderValue = float(security.Price)

            # orderFees = security.FeeModel.GetOrderFee(security, order)
            orderFees = self.GetOrderFee(orderValue, orderQuantity)
            self.Debug("order: Quantity={}, Value={}, Fees={}".format(orderQuantity, orderValue, orderFees))

            # find an incremental delta value for the next iteration step
            feeToPriceRatio = orderFees / unit_price
            feeToPriceRatio -= feeToPriceRatio % lot_size
            if feeToPriceRatio < lot_size:
                feeToPriceRatio = lot_size

            # calculate the margin required for the order
            # marginRequired = security.MarginModel.GetInitialMarginRequiredForOrder(security, order)

            # if marginRequired <= marginRemaining and orderValue + orderFees <= targetOrderValue:
            if orderValue + orderFees <= targetOrderValue:
                break

        # add directionality back in
        return -orderQuantity if direction == OrderDirection.Sell else orderQuantity


    def GetOrderFee(self, price_per_share, qty):
        tradeValue = abs(price_per_share * qty)
        fee_per_share = 0.005
        tradeFee = abs(fee_per_share * qty)

        # Maximum Per Order: 0.5%
        # Minimum per order: $1.0
        maximumPerOrder = fee_per_share * tradeValue
        minimumPerOrder = 1.0
        tradeFee = min(tradeFee, maximumPerOrder)
        tradeFee = max(tradeFee, minimumPerOrder)
        return tradeFee


class BenchmarkSymbol(object):
    def __init__(self, ticker, name=None, crypto=False):
        self.Name = name or ticker
        if crypto:
            self._symbol = Singleton.QCAlgorithm.AddCrypto(ticker, Resolution.Daily).Symbol
        else:
            self._symbol = Singleton.QCAlgorithm.AddEquity(ticker, Resolution.Daily).Symbol
        self._cost = 0

    @property
    def Performance(self):
        if self._cost == 0:
            self._cost = float(Singleton.QCAlgorithm.Securities[self._symbol.Value].Price)
        price = float(Singleton.QCAlgorithm.Securities[self._symbol.Value].Price)
        if price == 0 or self._cost == 0:
            return 0.0
        return 100.0 * ((price / self._cost) - 1.0)


class InternalOrder(object):
    @accepts(self=object, portfolio=Portfolio, symbol=Symbol, quantity=(int, float), order_type=int,
             limit_price=(float, None), stop_price=(float, None), tag=str)
    def __init__(self, portfolio, symbol, quantity, order_type=OrderType.Market,
                 limit_price=None, stop_price=None, tag=""):
        self.Portfolio = portfolio
        self.Symbol = symbol
        self.Quantity = quantity # Requested quantity
        self.OrderType = order_type
        self.LimitPrice = limit_price
        self.StopPrice = stop_price
        self.tag = tag
        self.Ticket = None

    def __hash__(self):
        return hash((self.Portfolio, self.Symbol, self.Quantity, self.OrderType, self.LimitPrice,
                     self.StopPrice, self.Ticket))

    def __eq__(self, other):
        return (self.Portfolio, self.Symbol,
                self.Quantity, self.OrderType, self.LimitPrice,
                self.StopPrice, self.Ticket) == (other.Portfolio, other.Symbol,
                                                 other.Quantity, other.OrderType, other.LimitPrice,
                                                 other.StopPrice, other.Ticket)

    def __ne__(self, other):
        return not self == other

    def ToString(self):
        return "{0} order for {1} units of {2}".format(
            InternalOrder.TypeToString(self.OrderType), self.Quantity, self.Symbol)

    def __str__(self):
        return self.ToString()

    def __repr__(self):
        return self.ToString()

    @classmethod
    def TypeToString(cls, order_type):
        if order_type is OrderType.Market: return "Market"
        elif order_type is OrderType.Limit: return "Limit"
        elif order_type is OrderType.StopMarket: return "StopMarket"
        elif order_type is OrderType.StopLimit: return "StopLimit"
        elif order_type is OrderType.MarketOnOpen: return "MarketOnOpen"
        elif order_type is OrderType.MarketOnClose: return "MarketOnClose"
        elif order_type is OrderType.OptionExercise: return "OptionExercise"


class Broker(object):
    def __init__(self, cash=0.0):
        self.Portfolio = Portfolio(broker=self, cash=cash)
        self._to_submit = []
        self.submitted = {}
        self.Log = Singleton.Log
        self.Debug = Singleton.Debug
        self.Error = Singleton.Error
        if Singleton.QCAlgorithm.LiveMode:
            self._loadFromBroker()

    def __str__(self):
        return "To Submit: %s; Submitted: %s" % (self._to_submit, self.submitted)

    def __repr__(self):
        return self.__str__()

    def _loadFromBroker(self):
        if Singleton.QCAlgorithm.Portfolio.Invested:
            self.Debug("_loadFromBroker")
            positions = [x for x in Singleton.QCAlgorithm.Portfolio.Securities
                         if x.Value.Holdings.AbsoluteQuantity != 0]
            for position in positions:
                cost = float(position.Value.Holdings.AveragePrice)
                qty = float(position.Value.Holdings.AbsoluteQuantity)
                symb = position.Key
                self.Portfolio[symb] = Position(symb, qty, cost)

        self.selfCheck()

    def selfCheck(self):
        real_funds = self.Portfolio.TotalPortfolioValue
        virtual_funds = sum(x.Portfolio.TotalPortfolioValue for x in Singleton.QCAlgorithm.algorithms)
        if virtual_funds > real_funds:
            message = "Insufficient funds in real portfolio ($%.2f) \
                      to support running algorithms ($%.2f)."                                                                                                                           % (real_funds, virtual_funds)
            self.Debug("EXCEPTION: %s" % message)
            raise Exception(message)

    @accepts(self=object, order=InternalOrder)
    def AddOrder(self, order):
        self._to_submit.append(order)

    def executeOrders(self):
        self._minimizeOrders()
        self._executeOrdersOnPortfolio()
        self._executeOrdersOnBroker()

    def _minimizeOrders(self):
        pass

    def _executeOrdersOnPortfolio(self):
        remaining_orders = []
        for order in self._to_submit:
            filled_order = False
            symbol = order.Symbol
            if order.OrderType == OrderType.Market and order.Symbol in self.Portfolio:
                current_quantity = self.Portfolio[symbol].Quantity
                price_per_share = float(Singleton.QCAlgorithm.Securities[symbol.Value].Price)
                if order.Quantity < current_quantity:
                    order.Portfolio.FillOrder(symbol, order.Quantity, price_per_share)
                    self.Portfolio.FillOrder(symbol, -order.Quantity, price_per_share)
                    filled_order = True
                else:
                    order.Portfolio.FillOrder(symbol, current_quantity, price_per_share)
                    self.Portfolio.FillOrder(symbol, -current_quantity, price_per_share)
                    order.Quantity -= current_quantity

            if not filled_order:
                remaining_orders.append(order)

        self.Portfolio.CashBook = 0.0 # We don't use this cash
        self._to_submit = remaining_orders


    def _executeOrdersOnBroker(self):
        while any(self._to_submit):
            order = self._to_submit.pop(0)
            symb = order.Symbol
            qty = order.Quantity
            price_per_share = Singleton.QCAlgorithm.Securities[symb.Value].Price

            self.Debug("Submitting a %s (est: $%.2f/share)" % (order, price_per_share))

            market_is_open = Singleton.QCAlgorithm.Securities[symb.Value].Exchange.DateTimeIsOpen(
                Singleton.Time)

            # Submit order.
            if order.OrderType == OrderType.Market:
                asynchronous = False
                if qty < 0:
                    asynchronous = False
                if market_is_open:
                    ticket = Singleton.QCAlgorithm.MarketOrder(symb, qty, asynchronous, order.tag)
                else:
                    ticket = Singleton.QCAlgorithm.MarketOnOpenOrder(symb, qty, order.tag)
            elif order.OrderType == OrderType.Limit:
                ticket = Singleton.QCAlgorithm.LimitOrder(symb, qty, order.LimitPrice, order.tag)
            elif order.OrderType == OrderType.StopMarket:
                ticket = Singleton.QCAlgorithm.StopMarketOrder(symb, qty, order.StopPrice, order.tag)
            elif order.OrderType == OrderType.StopLimit:
                ticket = Singleton.QCAlgorithm.StopLimitOrder(symb, qty, order.StopPrice, order.LimitPrice, order.tag)
            elif order.OrderType == OrderType.MarketOnOpen:
                ticket = Singleton.QCAlgorithm.MarketOnOpenOrder(symb, qty, order.tag)
            elif order.OrderType == OrderType.MarketOnClose:
                ticket = Singleton.QCAlgorithm.MarketOnCloseOrder(symb, qty, order.tag)
            elif order.OrderType == OrderType.OptionExercise:
                ticket = Singleton.QCAlgorithm.OptionExerciseOrder(symb, qty, order.tag)

            # Handle synchronous orders
            if ticket.Status in [OrderStatus.Filled, OrderStatus.PartiallyFilled]:
                self.Debug("Order was filled synchronously!")
                for order_event in ticket.OrderEvents:
                    qty -= float(order_event.FillQuantity)
                    order.Portfolio.ProcessOrderEvent(order_event, order)
                    # TODO: call alg.OnOrderEvent()

            if qty != 0:
                # Update order with ticket.
                order.Quantity = qty
                order.Ticket = ticket
                self.submitted[ticket.OrderId] = order

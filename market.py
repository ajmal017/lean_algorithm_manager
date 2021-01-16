# pylint: disable=C0321,W0401,W0614
try: QCAlgorithm
except NameError: from mocked import *

from decimal import Decimal
from datetime import date
from math import isclose
from decorators import accepts, convert_to_symbol
from singleton import Singleton

# pylint: disable=C0111,C0103,C0112,E1136,R0903,R0913,R0914,R0902,R0911


class Helper:
    @classmethod
    def is_order_done(cls, event_order_status):
        if event_order_status in (
            OrderStatus.New,
            OrderStatus.Submitted,
            OrderStatus.CancelPending,
            OrderStatus.UpdateSubmitted
        ):
            return False
        else:
            return True

class ISymbolDict(dict):
    # def __iter__(self):
    #     return super().items().__iter__()

    @accepts(self=object, key=(Symbol, str), value=object)
    def __setitem__(self, key, value):
        key = ISymbolDict.CreateSymbol(key)
        return super().__setitem__(key, value)

    @accepts(self=object, key=(Symbol, str))
    def __getitem__(self, key):
        key = ISymbolDict.CreateSymbol(key)
        if key not in self:
            return self.NoValue(key)
        return super().__getitem__(key)

    @classmethod
    def CreateSymbol(cls, key):
        if isinstance(key, Symbol):
            return key
        elif isinstance(key, str):
            return Singleton.QCAlgorithm.Securities[key].Symbol
        else:
            raise TypeError("Expected str or Symbol, but got {}".format(key))

    def NoValue(self, key):
        raise KeyError("Could not find key \"{}\"".format(key))

    @property
    def Keys(self):
        return self.keys()

    @property
    def Values(self):
        return self.values()


class Position(object):
    '''SecurityHolding'''

    @accepts(self=object, symbol=Symbol, quantity=(int, float), price_per_share=(int, float), fees=(int, float))
    def __init__(self, symbol, quantity, price_per_share, fees=0):
        self.Symbol = symbol
        self.Quantity = float(quantity)
        self.AveragePrice = float(price_per_share)
        self.TotalFees = float(fees)
        self.Security = None
        if symbol in Singleton.QCAlgorithm.Securities:
            self.Security = Singleton.QCAlgorithm.Securities[symbol]


    def __str__(self):
        return "(%.1f %s @ %.2f USD + $%.2f)" % (self.Quantity, self.Symbol, self.HoldingsCost(), self.TotalFees)

    def __repr__(self):
        return f"{self.Symbol}: {self.Quantity}"

    @property
    def AbsoluteQuantity(self):
        return abs(self.Quantity)


    def HoldingsCost(self):
        return self.Quantity * self.AveragePrice

    @property
    def HoldStock(self):
        return self.AbsoluteQuantity > 0

    @property
    def Invested(self):
        return self.HoldStock

    @property
    def IsLong(self):
        return self.Quantity > 0.0

    @property
    def IsShort(self):
        return self.Quantity < 0.0

    # @property
    # def NetProfit(self):
    #     return self.Profit - self.TotalFees

    @property
    def Price(self):
        return self.Security.Price

    @accepts(self=object, quantity=float, price_per_share=float, fees=float)
    def _fill(self, quantity, price_per_share=None, fees=0.0):
        if quantity == 0:
            return

        if quantity > 0:
            old_sum = self.Quantity * self.AveragePrice
            new_sum = quantity * price_per_share
            self.Quantity += quantity
            self.AveragePrice = (old_sum + new_sum) / self.Quantity

        elif quantity < 0:
            self.Quantity += quantity

        self.TotalFees += fees


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



class Portfolio(ISymbolDict):
    '''SecurityPortfolioManager'''
    def __init__(self, algorithm=None, cash=0.0):
        super().__init__()
        self.Algorithm = algorithm
        self.__orders = []
        self.__cost = cash
        self.Cash = Cash('USD', cash)
        self.CashBook = CashBook()
        self.CashBook['USD'] = Cash('USD', cash)
        self.UnsettledCash = 0.0

    def __bool__(self):
        return True

    def NoValue(self, key):
        return Position(key, 0, 0)

    def SetCost(self, cost):
        self.__cost = cost

    def SetCash(self, cash):
        self.Cash = Cash('USD', cash)
        self.CashBook['USD'] = Cash('USD', cash)
        self.SetCost(cash)

    @property
    def HoldStock(self):
        return self.TotalHoldingsValue > 0

    @property
    def Invested(self):
        for pos in self.values():
            if pos.Quantity > 0:
                return True
        return False

    @property
    def TotalPortfolioValue(self):
        return self.TotalHoldingsValue + self.Cash + self.UnsettledCash

    @property
    def TotalHoldingsValue(self):
        retval = sum([(pos.Quantity) * Singleton.QCAlgorithm.Securities[symb].Price
                      for symb, pos in iter(self.items())])
        return float(retval)

    @property
    def TotalHoldingsCost(self):
        return sum([pos.Quantity * pos.AveragePrice for pos in iter(self.values())])

    @property
    def UnrealizedProfit(self):
        return self.TotalHoldingsValue - self.TotalHoldingsCost

    @property
    def Performance(self):
        if self.__cost == 0:
            return 0.0
        return round(100.0 * ((self.TotalPortfolioValue / self.__cost) - 1.0), 2)

    # @property
    # def TotalProfit(self):
    #     return sum([pos.Profit for pos in self.values()])

    @property
    def TotalFees(self):
        retval = sum([pos.TotalFees for pos in self.values()])
        return retval

    def __str__(self):
        return Portfolio.ToString(self)

    def __repr__(self):
        return "{" + ", ".join(map(repr, self.values())) + "}"

    @classmethod
    def ToString(cls, portfolio):
        positions = [f"({symb.Value}, {pos.Quantity})" for symb, pos in portfolio.items()]
        text_positions = (", ".join(positions))
        return \
            f"[{text_positions}], " \
            f"TotalHoldingsValue: {round(portfolio.TotalHoldingsValue, 2)}, " \
            f"Cash: {round(portfolio.Cash, 2)}, " \
            f"UnsettledCash: {round(portfolio.UnsettledCash, 2)}, " \
            f"TotalFees: {round(portfolio.TotalFees, 2)}"

    @accepts(self=object, order_event=OrderEvent, order=object)
    def ProcessFill(self, order_event, order):
        Singleton.Debug("> ProcessFill: %s" % order_event)
        self._fill_order(order.Symbol, order_event.FillQuantity, order_event.FillPrice, order_event.OrderFee.Value.Amount)

    @accepts(self=object, symbol=Symbol, quantity=float, price_per_share=float, fees=float)
    def _fill_order(self, symbol, quantity, price_per_share, fees=0.0):
        """Used by Broker."""
        if symbol not in self:
            self[symbol] = Position(symbol, quantity, price_per_share, fees)
        else:
            self[symbol]._fill(quantity, price_per_share, fees)
        self.Cash -= quantity * price_per_share
        self.Cash -= fees
        self.CashBook['USD'] = self.Cash

        # We round the float to prevent negative near-zero
        remaining_quantity = round(self[symbol].Quantity, 6)
        if remaining_quantity < 0:
            message = "Negative positions of %s (%f)" % (symbol, remaining_quantity)
            raise Exception(message)

    # @accepts(self=object, order=InternalOrder)
    def AddOrder(self, order):
        Singleton.Debug(f"Portfolio.AddOrder: {order}")
        Singleton.Log(f"Order size: {order.Quantity}")
        Singleton.Log(f"isclose({order.Quantity}, 0, abs_tol={Singleton.Securities[order.Symbol].SymbolProperties.LotSize})")
        if isclose(order.Quantity, 0, abs_tol=Singleton.Securities[order.Symbol].SymbolProperties.LotSize):
            Singleton.Log("Warning: Avoiding submitting order that has zero quantity.")
            return
        Singleton.Debug(f"AddOrder: {order}")
        self.__orders.append(order)

    def ExecuteOrders(self):
        sorted_orders = sorted(self.__orders, key=lambda x: x.Quantity)
        for order in sorted_orders:
            Singleton.Broker.ExecuteOrder(order)
        self.__orders = []

    @convert_to_symbol('symbol', Singleton.CreateSymbol)
    def createOrder(self, symbol, quantity, order_type, **kwargs):
        order = InternalOrder(portfolio=self, symbol=symbol, quantity=quantity,
                              order_type=order_type, **kwargs)
        return self.AddOrder(order)

    def liquidate(self, symbol=None, tag="", immediately=False):
        if symbol is None:
            symbols = [sym for sym, pos in iter(self.items()) if pos.Quantity > 0]
            for s in symbols:
                self.liquidate(symbol=s, tag=tag, immediately=immediately)
        else:
            order = InternalOrder(portfolio=self, symbol=symbol, quantity=-self[symbol].Quantity, tag=tag)
            if immediately:
                Singleton.Broker.ExecuteOrder(order)
            else:
                self.AddOrder(order)



class BenchmarkSymbol(object):
    def __init__(self, ticker, name=None, security_type=SecurityType.Equity):
        self.Name = name or ticker
        self.__symbol = Singleton.QCAlgorithm.AddSecurity(security_type, ticker, Resolution.Daily).Symbol
        self.__cost = None # delay

    def Reset(self):
        self.__cost = Singleton.QCAlgorithm.Securities[self.__symbol.Value].Price

    @property
    def Performance(self):
        if Singleton.IsWarmingUp or (Singleton.QCAlgorithm.Portfolio.TotalHoldingsValue == 0.0 and Singleton.QCAlgorithm.Portfolio.TotalFees == 0.0):
            return 0.0

        if self.__cost == None:
            self.Reset()

        price = Singleton.QCAlgorithm.Securities[self.__symbol.Value].Price
        if price == 0 or self.__cost == 0:
            return 0.0
        return round(100.0 * ((price / self.__cost) - 1.0), 2)


class InternalOrder(object):
    @accepts(self=object, portfolio=Portfolio, symbol=Symbol, quantity=(int, float), order_type=int,
             limit_price=(int, float, None), stop_price=(int, float, None), tag=str)
    def __init__(self, portfolio, symbol, quantity, order_type=OrderType.Market,
                 limit_price=None, stop_price=None, tag=""):
        self.Portfolio = portfolio
        self.Symbol = symbol
        self.OrderType = order_type
        self.Quantity = float(quantity)
        self.LimitPrice = float(limit_price) if limit_price else None
        self.StopPrice = float(stop_price) if stop_price else None
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
        return f"{InternalOrder.TypeToString(self.OrderType)}Order({self.Symbol}, {self.Quantity})"

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
    def __init__(self, portfolio=None):
        self._submitted = {}
        # unmanaged cash and positions
        self.Portfolio = Portfolio() if portfolio is None else portfolio

    def __str__(self):
        return f"Submitted: {self._submitted}\nPortfolio: {self.Portfolio}"

    def __repr__(self):
        return self.__str__()

    def ImportFromBroker(self, currency='USD'):
        qc = Singleton.QCAlgorithm
        qc.Log("sync started")

        crypto_codes = ['BTC', 'ETH', 'LTC']
        qc.Log(f"Portfolio.CashBook.Keys: {qc.Portfolio.CashBook.Keys} ")

        cash_amount = qc.Portfolio.CashBook[currency].Amount
        self.Portfolio.SetCash(cash_amount)
        qc.Log(f"Portfolio.CashBook[{currency}].Amount: {cash_amount} ")

        for crypto_code in qc.Portfolio.CashBook.Keys:
            currency_pair = f"{crypto_code}{currency}"  # eg, BTCUSD
            qc.Log(f"Found {currency_pair} ({crypto_code})")
            if crypto_code not in crypto_codes:
                qc.Log(f"Ignoring {currency_pair} ({crypto_code})")
                continue
            cash = qc.Portfolio.CashBook[crypto_code]
            symbol = ISymbolDict.CreateSymbol(currency_pair)
            qty = cash.Amount
            qc.Log(f"Found {cash.Amount} positions")
            if qty == 0:
                qc.Log(f"Found zero positions for {symbol.Value}")
            price = cash.ConversionRate
            self.Portfolio[symbol] = Position(symbol, qty, price, fees=0.0)
            qc.Log(f"Imported from Singleton.Portfolio.CashBook: {cash} ")

        for symbol, position in qc.Portfolio.items():
            qty = position.Quantity
            if qty == 0:
                qc.Log(f"Found zero positions for {symbol.Value}")
                continue
            price = position.AveragePrice
            position = Position(symbol, qty, price, fees=0.0)
            self.Portfolio[symbol] = position
            qc.Log(f"Imported from Singleton.Portfolio {position} ")

        qc.Log("sync done")

    # @accepts(self=object, order=InternalOrder)
    def ExecuteOrder(self, order):
        qc = Singleton.QCAlgorithm
        qc.Log(f"Executing order for {order.Quantity}")
        if order.Quantity > 0:
            original_qty = order.Quantity
            self._execute_order_from_portfolio_if_needed(order)
            filled = original_qty = order.Quantity
            qc.Log(f"Filled {original_qty} from local portfolio")
            if order.Quantity == 0:
                return

        qc.Log(f"Executing order for {order.Quantity} from external brokerage")
        if not qc.LiveMode:
            self._execute_order(order)

    def _fill_order_from_portfolio(self, order):
        symbol = order.Symbol
        price_per_share = Singleton.QCAlgorithm.Securities[symbol.Value].Price
        ask = order.Quantity
        existing = self.Portfolio[symbol].Quantity
        fill_qty = min(ask, existing)
        self.Portfolio._fill_order(symbol, -fill_qty, price_per_share)
        order.Portfolio._fill_order(symbol, fill_qty, price_per_share)
        order.Quantity -= fill_qty

    def _execute_order_from_portfolio_if_needed(self, order):
        if order.Symbol in self.Portfolio:
            self._fill_order_from_portfolio(order)
            if order.Quantity == 0:
                return

        price_per_share = Singleton.QCAlgorithm.Securities[order.Symbol.Value].Price
        estimated_cost = order.Quantity *  price_per_share
        available_cash = Singleton.Broker.Portfolio.Cash
        if estimated_cost > available_cash and self.Portfolio.Invested:
            self.Portfolio.liquidate(immediately=True)

    def _execute_order(self, order):
        symb = order.Symbol
        qty = order.Quantity

        market_is_open = Singleton.QCAlgorithm.Securities[symb.Value].Exchange.ExchangeOpen

        # Submit order.
        if order.OrderType == OrderType.Market:
            if market_is_open:
                ticket = Singleton.QCAlgorithm.MarketOrder(symb, float(qty), False, order.tag)
            else:
                ticket = Singleton.QCAlgorithm.MarketOnOpenOrder(symb, float(qty), order.tag)
        elif order.OrderType == OrderType.Limit:
            ticket = Singleton.QCAlgorithm.LimitOrder(symb, float(qty), order.LimitPrice, order.tag)
        elif order.OrderType == OrderType.StopMarket:
            ticket = Singleton.QCAlgorithm.StopMarketOrder(symb, float(qty), order.StopPrice, order.tag)
        elif order.OrderType == OrderType.StopLimit:
            ticket = Singleton.QCAlgorithm.StopLimitOrder(symb, float(qty), order.StopPrice, order.LimitPrice, order.tag)
        elif order.OrderType == OrderType.MarketOnOpen:
            ticket = Singleton.QCAlgorithm.MarketOnOpenOrder(symb, float(qty), order.tag)
        elif order.OrderType == OrderType.MarketOnClose:
            ticket = Singleton.QCAlgorithm.MarketOnCloseOrder(symb, float(qty), order.tag)
        elif order.OrderType == OrderType.OptionExercise:
            ticket = Singleton.QCAlgorithm.OptionExerciseOrder(symb, float(qty), order.tag)

        # Handle synchronous orders
        order_is_done = Helper.is_order_done(ticket.Status)
        for order_event in ticket.OrderEvents:
            if order_is_done:
                order.Portfolio.ProcessFill(order_event, order)
                order.Portfolio.Algorithm.OnOrderEvent(order_event)
                order.Portfolio.Algorithm.TotalOrders += 1

        if not order_is_done:
            order.Ticket = ticket
            self._submitted[ticket.OrderId] = order

    @accepts(self=object, order_event=OrderEvent)
    def HandleOrderEvent(self, order_event):
        Singleton.Debug(f"> HandleOrderEvent (1): OrderEvent: {order_event}")
        order = self._submitted.pop(order_event.OrderId, None)
        if not order:
            Singleton.Debug(f"Could not find order id {order_event.OrderId} in queue: {self._submitted}")
            return

        Singleton.Debug(f"> HandleOrderEvent (2): Order: {order}")
        if Helper.is_order_done(order_event.Status):
            order.Portfolio.ProcessFill(order_event, order)
            order.Portfolio.Algorithm.OnOrderEvent(order_event)
            order.Portfolio.Algorithm.TotalOrders += 1

        else:
            # Re-add orders that are still open.
            self._submitted[order_event.OrderId] = order

    def GetOrderIdsForPortfolio(self, matching_portfolio):
        return [order_id for order_id, order in self._submitted.items() if order.Portfolio == matching_portfolio]

"""
MD5: 15d847147ab511e5249e614d15c19149
"""

# pylint: disable=C0321
try: QCAlgorithm
except NameError: from mocked import OrderType, Resolution

# pylint: disable=C0111,C0103,C0112,E1136,R0903,R0913,R0914,R0902,R0911
class Position(object):
    def __init__(self, symbol, quantity, price_per_share):
        self.Symbol = symbol
        self.Quantity = float(quantity)
        self.AveragePrice = float(price_per_share)

    def __str__(self):
        return "%sx%.1f ($%.2f)" % (self.Symbol, self.Quantity, self.TotalCost())

    def TotalCost(self):
        return self.Quantity * self.AveragePrice

    def Fill(self, quantity, price_per_share=None):
        if quantity == 0:
            return
        elif quantity < 0:
            price_per_share = self.AveragePrice

        self._fill(quantity, price_per_share)

    def _fill(self, quantity, price_per_share):
        denominator = self.Quantity + quantity
        if denominator == 0:
            self.AveragePrice = 0
            self.Quantity = 0
            return
        old_sum = self.Quantity * self.AveragePrice
        new_sum = (old_sum + quantity * price_per_share)
        self.AveragePrice = new_sum / denominator
        self.Quantity += quantity


class Portfolio(dict):
    def __init__(self, parent, broker, cash=0):
        super(Portfolio, self).__init__()
        self._parent = parent
        self._broker = broker
        self._initial_value = cash
        self.Cash = cash
        self.TotalFees = 0

    def __getitem__(self, key):
        if key not in self:
            return Position(None, 0, 0.0)
        return super(Portfolio, self).__getitem__(key)

    @property
    def Invested(self):
        return any(self)

    @property
    def TotalPortfolioValue(self):
        return self.TotalHoldingsValue + self.Cash - self.TotalFees

    @property
    def TotalHoldingsValue(self):
        return sum([pos.Quantity * float(self._parent.Securities[symb.Value].Price)
                    for symb, pos in self.iteritems()])

    @property
    def TotalHoldingsCost(self):
        return sum([pos.Quantity * pos.AveragePrice for _symb, pos in self.iteritems()])

    @property
    def UnrealizedProfit(self):
        return self.TotalHoldingsValue - self.TotalHoldingsCost

    @property
    def Performance(self):
        return 100.0 * ((self.TotalPortfolioValue / self._initial_value) - 1.0)

    @property
    def Profit(self):
        return self.TotalPortfolioValue - self._initial_value

    def __str__(self):
        sb = []
        for _, pos in self.iteritems():
            sb.append(str(pos))
        return 'Portfolio(' + ', '.join(sb) + ')'


    def FillOrder(self, symbol, quantity, price_per_share, fees=0.0):
        """Used by Broker."""
        if symbol not in self:
            self[symbol] = Position(symbol, quantity, price_per_share)
        else:
            self[symbol].Fill(quantity, price_per_share)

        self.Cash -= quantity * price_per_share
        self.TotalFees += fees

        remaining_quantity = self[symbol].Quantity
        if remaining_quantity < 0:
            message = "Order removed too many positions of %s" % symbol
            self._parent.Log("EXCEPTION: %s" % message)
            raise Exception, message
        elif remaining_quantity == 0:
            self.pop(symbol)

    def AddOrder(self, order):
        if order.Quantity == 0:
            self._parent.Log("Warning: Avoiding submitting order that has zero quantity.")
            return
        return self._broker.AddOrder(order)

    def Liquidate(self, symbol=None, tag=""):
        if symbol not in self:
            symbols = [sym for sym, pos in self.iteritems() if pos.Quantity > 0]
            for s in symbols:
                self.Liquidate(symbol=s, tag=tag)
        else:
            order = Order(self, symbol, -self[symbol].Quantity, tag=tag)
            self._broker.AddOrder(order)

    def GenerateOrder(self, symbol, target_alloc, tag=""):
        need_to_buy_qty = self._calculateOrderQuantity(symbol, target_alloc)
        return Order(self, symbol, need_to_buy_qty, tag=tag)

    def _calculateOrderQuantity(self, symbol, percentage):
        old_qty = self[symbol].Quantity
        if percentage == 0.0:
            return -old_qty

        price_per_share = float(self._parent.Securities[symbol.Value].Price)
        if price_per_share == 0.0:
            self._parent.Log("Could not get price of {} - NO ORDER".format(symbol.Value))
            return 0

        current_total_value = self.TotalPortfolioValue
        target_value = percentage * current_total_value
        current_value = old_qty * price_per_share

        need_to_buy_value = target_value - current_value
        return need_to_buy_value / price_per_share



class BenchmarkSymbol(object):
    def __init__(self, parent, ticker):
        self.Name = ticker
        self._parent = parent
        self._symbol = self._parent.AddEquity(ticker, Resolution.Daily).Symbol
        self._cost = None

    @property
    def Performance(self):
        if self._cost is None:
            self._cost = float(self._parent.Securities[self._symbol.Value].Price)
        price = float(self._parent.Securities[self._symbol.Value].Price)
        return 100.0 * ((price / self._cost) - 1.0)


class Order(object):
    def __init__(self, portfolio, symbol, quantity, order_type=OrderType.Market,
                 limit_price=None, stop_price=None, tag=""):
        self.Portfolio = portfolio
        self.Symbol = symbol
        self.Quantity = quantity
        self.Type = order_type
        self.LimitPrice = limit_price
        self.StopPrice = stop_price
        # self.Status = status
        self.tag = tag
        self.Ticket = None

    def __hash__(self):
        return hash((self.Portfolio, self.Symbol, self.Quantity, self.Type, self.LimitPrice,
                     self.StopPrice, self.Ticket))

    def __eq__(self, other):
        return (self.Portfolio, self.Symbol,
                self.Quantity, self.Type, self.LimitPrice,
                self.StopPrice, self.Ticket) == (other.Portfolio, other.Symbol,
                                                 other.Quantity, other.Type, other.LimitPrice,
                                                 other.StopPrice, other.Ticket)

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return "%sOrder(%s x %.1f)" % (Order.TypeToString(self.Type), self.Symbol, self.Quantity)

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
    def __init__(self, parent):
        self._parent = parent
        self.Portfolio = Portfolio(parent, self)
        self._to_submit = []
        self.submitted = {}
        if self._parent.LiveMode:
            self._loadFromBroker()

    def __str__(self):
        return "To Submit: %s; Submitted: %s" % (self._to_submit, self.submitted)

    def __repr__(self):
        return self.__str__()


    def _loadFromBroker(self):
        if self._parent.Portfolio.Invested:
            self._parent.Debug("updateBroker")
            positions = [x for x in self._parent.Portfolio.Securities
                         if x.Value.Holdings.AbsoluteQuantity != 0]
            for position in positions:
                cost = float(position.Value.Holdings.AveragePrice)
                qty = float(position.Value.Holdings.AbsoluteQuantity)
                symb = position.Key
                self.Portfolio[symb] = Position(symb, qty, cost)

        self.selfCheck()

    def selfCheck(self):
        real_funds = self.Portfolio.TotalPortfolioValue
        virtual_funds = sum(x.Portfolio.TotalPortfolioValue for x in self._parent.algorithms)
        if virtual_funds > real_funds:
            message = "Insufficient funds in real portfolio ($%.2f) \
                      to support running algorithms ($%.2f)." % (real_funds, virtual_funds)
            self._parent.Log("EXCEPTION: %s" % message)
            raise Exception, message

    def AddOrder(self, order):
        self._to_submit.append(order)
        return order

    def executeOrders(self):
        self._executeOrdersOnUnusedPortfolio()
        self._executeOrdersOnBroker()

    def _minimizeOrders(self):
        pass

    def _executeOrdersOnUnusedPortfolio(self):
        remaining_orders = []
        for order in self._to_submit:
            symbol = order.Symbol
            if order.Type == OrderType.Market and order.Symbol in self.Portfolio:
                position = self.Portfolio[symbol]

                avail_qty = position.Quantity
                price_per_share = float(self._parent.Securities[symbol.Value].Price)
                if price_per_share == 0.0:
                    continue

                if order.Quantity < avail_qty:
                    order.Portfolio.FillOrder(symbol, order.Quantity, price_per_share)
                    self.Portfolio.FillOrder(symbol, -order.Quantity, price_per_share)
                    continue
                else:
                    order.Portfolio.FillOrder(symbol, avail_qty, price_per_share)
                    self.Portfolio.FillOrder(symbol, -avail_qty, price_per_share)
                    order.Quantity -= avail_qty

            remaining_orders.append(order)

        self.Portfolio.Cash = 0
        self._to_submit = remaining_orders


    def _executeOrdersOnBroker(self):
        while any(self._to_submit):
            order = self._to_submit.pop(0)
            symb = order.Symbol
            qty = order.Quantity
            price_per_share = self._parent.Securities[symb.Value].Price

            self._parent.Log("Submitting a %s (est: $%.2f/share)" % (order, price_per_share))

            # Submit order.
            if order.Type == OrderType.Market:
                if qty < 0:
                    ticket = self._parent.MarketOrder(symb, qty, True, order.tag)
                else:
                    ticket = self._parent.MarketOrder(symb, qty, False, order.tag)
            elif order.Type == OrderType.Limit:
                ticket = self._parent.LimitOrder(symb, qty, order.LimitPrice, order.tag)
            elif order.Type == OrderType.StopMarket:
                ticket = self._parent.StopMarketOrder(symb, qty, order.StopPrice, order.tag)
            elif order.Type == OrderType.StopLimit:
                ticket = self._parent.StopLimitOrder(symb, qty, order.StopPrice, order.LimitPrice, order.tag)
            elif order.Type == OrderType.MarketOnOpen:
                ticket = self._parent.MarketOnOpenOrder(symb, qty, order.tag)
            elif order.Type == OrderType.MarketOnClose:
                ticket = self._parent.MarketOnCloseOrder(symb, qty, order.tag)
            elif order.Type == OrderType.OptionExercise:
                ticket = self._parent.OptionExerciseOrder(symb, qty, order.tag)

            # Update order with ticket.
            order.Ticket = ticket
            self.submitted[ticket.OrderId] = order

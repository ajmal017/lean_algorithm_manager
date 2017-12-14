"""
MD5: 2cc74b938279393c6eeab69f2a294fef
"""

# pylint: disable=C0321
try: QCAlgorithm
except NameError: from mocked import OrderType, OrderStatus, Symbol

# pylint: disable=C0111,C0103,C0112,E1136,R0903,R0913,R0914
class Position(object):
    def __init__(self, symbol, quantity, price_per_share):
        self.Symbol = symbol
        self.Quantity = float(quantity)
        self.AveragePrice = float(price_per_share)

    def __str__(self):
        return "%s=%.1f $%.2f" % (self.Symbol, self.Quantity, self.TotalCost())

    def TotalCost(self):
        return self.Quantity * self.AveragePrice

    def fill(self, quantity, price_per_share=None):
        if quantity < 0:
            price_per_share = self.AveragePrice
        self.__fill(quantity, price_per_share)

    def __fill(self, quantity, price_per_share):
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
        self.__parent = parent
        self.__broker = broker
        self.Cash = cash

    def __getattr__(self, attr):
        if attr == 'Invested':
            return any(self)
        else:
            raise AttributeError, attr

    def __str__(self):
        sb = []
        for _, pos in self.iteritems():
            sb.append(str(pos))
        return '(' + '), ('.join(sb) + ')'


    def fillOrder(self, symbol, quantity, price_per_share):
        """Used by Broker."""
        if symbol not in self:
            self[symbol] = Position(symbol, quantity, price_per_share)
        else:
            self[symbol].fill(quantity, price_per_share)

        self.Cash -= quantity * price_per_share

        remaining_quantity = self[symbol].Quantity
        if remaining_quantity < 0:
            raise Exception("Order removed too many positions of %s" % symbol)
        elif remaining_quantity == 0:
            self.pop(symbol)

    def addOrder(self, order):
        return self.__broker.addOrder(order)

    def Liquidate(self, symbol=None, tag=''):
        if symbol not in self:
            symbols = [sym for sym, pos in self.iteritems() if pos.Quantity > 0]
            for s in symbols:
                self.Liquidate(s)
        else:
            order = Order(self, symbol, -self[symbol].Quantity, tag=tag)
            self.__broker.addOrder(order)

    def getTotalValue(self):
        shares = sum([pos.Quantity * float(self.__parent.Securities[symb].Price)
                      for symb, pos in self.iteritems()])
        return self.Cash + shares

    def getTotalCost(self):
        shares = sum([pos.Quantity * pos.AveragePrice for _symb, pos in self.iteritems()])
        return self.Cash + shares

    def getOrdersForTargetAllocation(self, symbol, target_alloc, tag=""):
        orders = []

        old_qty = self[symbol].Quantity if symbol in self else 0.0
        price_per_share = float(self.__parent.Securities[symbol].Price)
        current_total_value = self.getTotalValue()
        target_value = float(target_alloc) * current_total_value
        current_value = old_qty * price_per_share

        need_to_buy_value = target_value - current_value
        need_to_buy_qty = need_to_buy_value / price_per_share
        order = Order(self, symbol, need_to_buy_qty, tag=tag)
        orders.append(order)

        remaining_cash = self.Cash - need_to_buy_value

        # Might need to make enough cash on remaining securities.
        if remaining_cash < 0.0:
            old_cash_alloc = self.Cash / self.getTotalValue()
            old_remaining_alloc = 1.0 - self.getCurrentAllocation(symbol) - old_cash_alloc
            new_remaining_alloc = 1.0 - target_alloc
            multiplier = new_remaining_alloc / old_remaining_alloc
            for symb, pos in self.iteritems():
                if symb != symbol:
                    new_qty = multiplier * pos.Quantity
                    order_qty = new_qty - pos.Quantity
                    order = Order(self, symb, order_qty, tag=tag)
                    orders.append(order)

        return orders

    def getCurrentAllocation(self, symbol):
        if symbol not in self: return 0.0
        shares_qty = self[symbol].Quantity
        price_per_share = float(self.__parent.Securities[symbol].Price)
        return (shares_qty * price_per_share) / self.getTotalValue()


class Order(object):
    def __init__(self, portfolio, symbol, quantity, order_type=OrderType.Market,
                 limit_price=None, stop_price=None, tag=""):
        self.Portfolio = portfolio
        self.Symbol = symbol
        self.Quantity = quantity
        self.LimitPrice = limit_price
        self.StopPrice = stop_price
        self.Type = order_type
        # self.Status = status
        self.tag = tag
        self.Ticket = None

    @classmethod
    def TypeToString(cls, order_type):
        if order_type is OrderType.Market: return "Market"
        elif order_type is OrderType.Limit: return "Limit"
        elif order_type is OrderType.StopMarket: return "StopMarket"
        elif order_type is OrderType.StopLimit: return "StopLimit"
        # else: return "?????"

    def __str__(self):
        return "%sOrder: %s=%.1f" % (Order.TypeToString(self.Type), self.Symbol, self.Quantity)


class Broker(object):
    def __init__(self, parent):
        self.__parent = parent
        self.Portfolio = Portfolio(parent, self)
        self.__to_submit = []
        self.submitted = {}
        if self.__parent.LiveMode:
            self.__loadFromBroker()


    def __loadFromBroker(self):
        if self.__parent.Portfolio.Invested:
            self.__parent.Debug("updateBroker")
            positions = [x for x in self.__parent.Portfolio.Securities
                         if x.Value.Holdings.AbsoluteQuantity != 0]
            for position in positions:
                cost = float(position.Value.Holdings.AveragePrice)
                qty = float(position.Value.Holdings.AbsoluteQuantity)
                symb = position.Key
                self.Portfolio[symb] = Position(symb, qty, cost)

        self.selfCheck()

    def selfCheck(self):
        real_funds = self.Portfolio.getTotalValue()
        virtual_funds = sum(x.Portfolio.getTotalValue() for x in self.__parent.algorithms)
        if virtual_funds > real_funds:
            raise Exception("Insufficient funds in real portfolio ($%.2f) "
                            "to support running algorithms ($%.2f)." % (real_funds, virtual_funds))

    def addOrder(self, order):
        self.__to_submit.append(order)
        return order

    def executeOrders(self):
        self.__executeOrdersOnUnusedPortfolio()
        self.__executeOrdersOnBroker()

    def __minimizeOrders(self):
        pass

    def __executeOrdersOnUnusedPortfolio(self):
        remaining_orders = []
        for order in self.__to_submit:
            symbol = order.Symbol
            if order.Type == OrderType.Market and \
                order.Symbol in self.Portfolio:
                position = self.Portfolio[symbol]

                avail_qty = position.Quantity
                price = float(self.__parent.Securities[symbol].Price)

                if order.Quantity < avail_qty:
                    order.Portfolio.fillOrder(symbol, order.Quantity, price)
                    self.Portfolio.fillOrder(symbol, -order.Quantity, price)
                    continue
                else:
                    order.Portfolio.fillOrder(symbol, avail_qty, price)
                    self.Portfolio.fillOrder(symbol, -avail_qty, price)
                    order.Quantity -= avail_qty

            remaining_orders.append(order)

        self.Portfolio.Cash = 0
        self.__to_submit = remaining_orders


    def __executeOrdersOnBroker(self):
        while any(self.__to_submit):
            order = self.__to_submit.pop()
            self.__parent.Debug("Handling %s" % order)

            symb = order.Symbol
            qty = int(order.Quantity)
            self.__parent.Debug("Converting quantity to %d" % qty)
            self.__parent.Debug("Submitting %s" % order)

            # Submit order.
            if order.Type == OrderType.Market:
                ticket = self.__parent.MarketOrder(symb, qty, False, order.tag)
            elif order.Type == OrderType.Limit:
                ticket = self.__parent.LimitOrder(symb, qty, order.LimitPrice, order.tag)
            elif order.Type == OrderType.StopMarket:
                ticket = self.__parent.StopMarketOrder(symb, qty, order.StopPrice, order.tag)
            elif order.Type == OrderType.StopLimit:
                ticket = self.__parent.StopLimitOrder(symb, qty, order.StopPrice, order.LimitPrice, order.tag)

            # Update order with ticket.
            order.Ticket = ticket
            self.submitted[ticket.OrderId] = order

            # Check order status.
            # if ticket.Status in [OrderStatus.Filled, OrderStatus.PartiallyFilled]:
            #     partial = "Partially" if ticket.Status == OrderStatus.PartiallyFilled else "Completely"
            #     self.__parent.Debug("%s Filled" % (partial))
            #     order.Portfolio.fillOrder(order.Symbol, float(ticket.FillQuantity), float(ticket.FillPrice))

            # elif ticket.Status in [OrderStatus.New, OrderStatus.Submitted]:
            #     self.submitted[ticket.OrderId] = order

            # elif ticket.Status in [OrderStatus.Canceled, OrderStatus.CancelPending]:
            #     self.__parent.Debug("Canceled/CancelPending")
            # else:
            #     raise Exception('%s: %s (Invalid!)' % (order, ticket.ToString()))

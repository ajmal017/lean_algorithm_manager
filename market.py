"""
MD5: 97d2b8b205b1b8c831e9be3dd4129ba8
"""

try: QCAlgorithm
except NameError: from mocked import OrderType, OrderStatus, Symbol

# pylint: disable=C0111,C0103,C0112,E1136
class Position(object):
    def __init__(self, symbol, quantity, price_per_share):
        self.Symbol = symbol
        self.Quantity = float(quantity)
        self.cost = float(price_per_share)

    def __str__(self):
        return "Position(Symbol: %s, Quantity: %f, Cost: %f" % (self.Symbol, self.Quantity, self.cost)

    def fill(self, quantity, price_per_share=None):
        if quantity < 0:
            price_per_share = self.cost
        self.__fill(quantity, price_per_share)

    def __fill(self, quantity, price_per_share):
        denominator = self.Quantity + quantity
        if denominator == 0:
            self.cost = 0
            self.Quantity = 0
            return
        old_sum = self.Quantity * self.cost
        new_sum = (old_sum + quantity * price_per_share)
        self.cost = new_sum / denominator
        self.Quantity += quantity


class Portfolio(dict):
    def __init__(self, parent, cash):
        super(Portfolio, self).__init__()
        self._parent = parent
        self.Cash = cash

    def __getattr__(self, attr):
        if attr == 'Invested':
            return any(self)
        else:
            raise AttributeError, attr

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

    def getTotalValue(self):
        shares = sum([pos.Quantity * float(self._parent.Securities[symb].Price)
                      for symb, pos in self.iteritems()])
        return self.Cash + shares

    def getTotalCost(self):
        shares = sum([pos.Quantity * pos.cost for symb, pos in self.iteritems()])
        return self.Cash + shares

    def getOrdersForTargetAllocation(self, symbol, target_alloc):
        orders = []

        if not isinstance(symbol, Symbol): import ipdb; ipdb.set_trace()

        old_qty = self[symbol].Quantity if symbol in self else 0.0
        price_per_share = float(self._parent.Securities[symbol].Price)
        current_total_value = self.getTotalValue()
        target_value = float(target_alloc) * current_total_value
        current_value = old_qty * price_per_share

        need_to_buy_value = target_value - current_value
        need_to_buy_qty = need_to_buy_value / price_per_share
        order = Order(self, symbol, need_to_buy_qty)
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
                    order = Order(self, symb, order_qty)
                    orders.append(order)

        return orders

    def getCurrentAllocation(self, symbol):
        if symbol not in self: return 0.0
        shares_qty = self[symbol].Quantity
        price_per_share = float(self._parent.Securities[symbol].Price)
        return (shares_qty * price_per_share) / self.getTotalValue()


class Order(object):
    def __init__(self, portfolio, symbol, quantity, order_type=OrderType.Market,
                 limit_price=None, stop_price=None, tag=""):
        if not isinstance(symbol, Symbol):
            import ipdb
            ipdb.set_trace()
        self.Portfolio = portfolio
        self.Symbol = symbol
        self.Quantity = quantity
        self.LimitPrice = limit_price
        self.StopPrice = stop_price
        self.Type = order_type
        # self.Status = status
        self.tag = tag

    @classmethod
    def TypeToString(cls, type):
        if type is OrderType.Market: return "market"
        elif type is OrderType.Limit: return "Limit"
        elif type is OrderType.StopMarket: return "StopMarket"
        elif type is OrderType.StopMarket: return "StopMarket"
        else: return "?????"

    def __str__(self):
        return "Order(Symbol: %s, Quantity: %f, Type: %s)" % (self.Symbol, self.Quantity, Order.TypeToString(self.Type))


class Broker(object):
    def __init__(self, parent, cash):
        self._parent = parent
        self.available = Portfolio(parent=parent, cash=cash)
        self.orders = []

    def addOrder(self, order):
        self.orders.append(order)
        return order

    def executeOrders(self):
        self.__executeOrdersOnUnusedPortfolio()
        self.__executeOrdersOnBroker()

    def __executeOrdersOnUnusedPortfolio(self):
        remaining_orders = []
        for order in self.orders:
            symbol = order.Symbol
            if order.Type == OrderType.Market and \
                order.Symbol in self.available:
                position = self.available[symbol]

                avail_qty = position.Quantity
                price = float(self._parent.Securities[symbol].Price)

                if order.Quantity < avail_qty:
                    self.available.fillOrder(symbol, -order.Quantity, price)
                    order.Portfolio.fillOrder(symbol, order.Quantity, price)
                    continue
                else:
                    self.available.fillOrder(symbol, -avail_qty, price)
                    order.Portfolio.fillOrder(symbol, avail_qty, price)
                    order.Quantity -= avail_qty

            remaining_orders.append(order)

        self.orders = remaining_orders


    def __executeOrdersOnBroker(self):
        while any(self.orders):
            order = self.orders.pop()
            self._parent.Debug("Handling %s" % order)

            symb = order.Symbol
            qty = int(order.Quantity)
            self._parent.Debug("Converting quantity to %d" % qty)

            # Submit order.
            if order.Type == OrderType.Market:
                ticket = self._parent.MarketOrder(
                    symb, qty, tag=order.tag)
            elif order.Type == OrderType.Limit:
                ticket = self._parent.LimitOrder(
                    symb, qty, order.LimitPrice, tag=order.tag)
            elif order.Type == OrderType.StopMarket:
                ticket = self._parent.StopMarketOrder(
                    symb, qty, order.StopPrice, tag=order.tag)
            elif order.Type == OrderType.StopLimit:
                ticket = self._parent.StopLimitOrder(
                    symb, qty, order.StopPrice, order.LimitPrice, tag=order.tag)

            # Check order status.
            if ticket.Status in [OrderStatus.Filled, OrderStatus.PartiallyFilled]:
                self._parent.Debug("Filled (partially? %s)" % (
                    ticket.Status == OrderStatus.PartiallyFilled))
                order.Portfolio.fillOrder(order.Symbol, float(ticket.FillQuantity),
                                          float(ticket.FillPrice))
            elif ticket.Status in [OrderStatus.New, OrderStatus.Submitted]:
                pass
            elif ticket.Status in [OrderStatus.Canceled, OrderStatus.CancelPending]:
                self._parent.Debug("Canceled/CancelPending")
            else:
                raise Exception('%s: %s (Invalid!)' % (order, ticket.ToString()))

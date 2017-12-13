"""
MD5: 3728ae61236a7980007ce6d4a81b4182
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
    def __init__(self, parent, cash=0):
        super(Portfolio, self).__init__()
        self._parent = parent
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

    def getTotalValue(self):
        shares = sum([pos.Quantity * float(self._parent.Securities[symb].Price)
                      for symb, pos in self.iteritems()])
        return self.Cash + shares

    def getTotalCost(self):
        shares = sum([pos.Quantity * pos.AveragePrice for _symb, pos in self.iteritems()])
        return self.Cash + shares

    def getOrdersForTargetAllocation(self, symbol, target_alloc, tag=""):
        orders = []

        if not isinstance(symbol, Symbol): import ipdb; ipdb.set_trace()

        old_qty = self[symbol].Quantity if symbol in self else 0.0
        price_per_share = float(self._parent.Securities[symbol].Price)
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
        self._parent = parent
        self.Portfolio = Portfolio(parent)
        self.orders = []
        self.submitted = {}
        if self._parent.LiveMode:
            self._loadFromBroker()


    def _loadFromBroker(self):
        self.Portfolio.Cash = self._parent.Portfolio.Cash
        if self._parent.Portfolio.Invested:
            self._parent.Debug("updateBroker")
            positions = [x for x in self._parent.Portfolio.Securities
                         if x.Value.Holdings.AbsoluteQuantity != 0]
            for position in positions:
                cost = float(position.Value.Holdings.AveragePrice)
                qty = float(position.Value.Holdings.AbsoluteQuantity)
                symb = position.Key
                self.Portfolio[symb] = Position(symb, qty, cost)

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
                order.Symbol in self.Portfolio:
                position = self.Portfolio[symbol]

                avail_qty = position.Quantity
                price = float(self._parent.Securities[symbol].Price)

                if order.Quantity < avail_qty:
                    self.Portfolio.fillOrder(symbol, -order.Quantity, price)
                    order.Portfolio.fillOrder(symbol, order.Quantity, price)
                    continue
                else:
                    self.Portfolio.fillOrder(symbol, -avail_qty, price)
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
            self._parent.Debug("Submitting %s" % order)

            # Submit order.
            if order.Type == OrderType.Market:
                ticket = self._parent.MarketOrder(symb, qty, False, order.tag)
            elif order.Type == OrderType.Limit:
                ticket = self._parent.LimitOrder(symb, qty, order.LimitPrice, order.tag)
            elif order.Type == OrderType.StopMarket:
                ticket = self._parent.StopMarketOrder(symb, qty, order.StopPrice, order.tag)
            elif order.Type == OrderType.StopLimit:
                ticket = self._parent.StopLimitOrder(symb, qty, order.StopPrice, order.LimitPrice, order.tag)

            # Check order status.
            if ticket.Status in [OrderStatus.Filled, OrderStatus.PartiallyFilled]:
                partial = "Partially" if ticket.Status == OrderStatus.PartiallyFilled else "Completely"
                self._parent.Debug("%s Filled" % (partial))
                order.Portfolio.fillOrder(order.Symbol, float(ticket.FillQuantity), float(ticket.FillPrice))
            elif ticket.Status in [OrderStatus.New, OrderStatus.Submitted]:
                self.submitted[ticket.OrderId] = order

            elif ticket.Status in [OrderStatus.Canceled, OrderStatus.CancelPending]:
                self._parent.Debug("Canceled/CancelPending")
            else:
                raise Exception('%s: %s (Invalid!)' % (order, ticket.ToString()))

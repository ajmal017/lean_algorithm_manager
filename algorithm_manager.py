"""
MD5: f8a163d11feff380aef25ccfbaa6be97
"""

# pylint: disable=C0321,C0111,W0201,C0413
try: QCAlgorithm
except NameError:
    from mocked import *  # pylint: disable=W0614,W0401
    from market import Broker

class AlgorithmManager(QCAlgorithm):

    @accepts(self=object, broker=Broker)
    def registerBroker(self, broker):
        self._broker = broker

    @accepts(self=object, algorithms=list, benchmarks=list)
    def registerAlgorithms(self, algorithms, benchmarks):
        self._warm_up_period = 0
        self._algorithms = algorithms
        self._benchmarks = benchmarks

        plot = Chart('Performance')
        for i in algorithms + benchmarks:
            plot.AddSeries(Series(i.Name, SeriesType.Line, 0, '%'))
        self.AddChart(plot)

    def _pre(self):
        pass

    def _post(self):
        # self._broker.executeOrders()
        pass

    def SetWarmUp(self, period):
        if period > self._warm_up_period:
            self._warm_up_period = period
            super(AlgorithmManager, self).SetWarmUp(period)

    def CoarseSelectionFunction(self, coarse):
        symbols = []
        for alg in self._algorithms:
            symbols.extend(alg.CoarseSelectionFunction(coarse))
        return symbols

    def FineSelectionFunction(self, fine):
        symbols = []
        for alg in self._algorithms:
            symbols.extend(alg.FineSelectionFunction(fine))
        return symbols

    def OnData(self, data):
        if self.IsWarmingUp: return
        # self.Log("OnData")
        self._pre()
        for alg in self._algorithms:
            alg.OnData(data)
        self._post()

    def OnDividend(self):
        if self.IsWarmingUp: return
        self.Log("OnDividend")
        self._pre()
        for alg in self._algorithms:
            alg.OnDividend()
        self._post()

    def OnSecuritiesChanged(self, changes):
        if self.IsWarmingUp: return
        self.Log("OnSecuritiesChanged {0}".format(changes))
        self._pre()
        for alg in self._algorithms:
            # Only call if there's a relevant stock in alg
            alg.OnSecuritiesChanged(changes)
        self._post()

    def OnEndOfDay(self):
        if self.IsWarmingUp: return
        # self.Log("OnEndOfDay")
        self._pre()
        for alg in self._algorithms:
            alg.OnEndOfDay()
        self._post()

        for i in self._algorithms + self._benchmarks:
            self.Plot('Performance', i.Name, i.Performance)

    def OnEndOfAlgorithm(self):
        self.Log("OnEndOfAlgorithm")
        self._pre()
        for alg in self._algorithms:
            alg.OnEndOfAlgorithm()
        self._post()

    def OnOrderEvent(self, event_order):
        self.Log("OnOrderEvent")
        order_id = event_order.OrderId
        ticket = self.Transactions.GetOrderById(order_id)
        self.Log("TICKET: {0}".format(ticket))

        if event_order.Status in [OrderStatus.Submitted, OrderStatus.New]:
            self.Log("SUBMITTED/NEW: {0}".format(ticket))

        else:
            if order_id in self._broker.submitted:
                order = self._broker.submitted.pop(order_id)
                self.Log("ORDER: {0}".format(order))
            else:
                order = None
                self.Log("ORDER: N/A")

            if event_order.Status == OrderStatus.Invalid:
                self.Log("INVALID: {0}".format(ticket))

            elif event_order.Status in [OrderStatus.Filled, OrderStatus.PartiallyFilled]:
                prefix = "PARTIALLY " if event_order.Status == OrderStatus.PartiallyFilled else ""
                self.Log("{0}FILLED: {1} at FILL PRICE: {2}".format(prefix, ticket, event_order.FillPrice))
                if order:
                    order.Portfolio.FillOrder(order.Symbol, float(event_order.FillQuantity),
                                              float(event_order.FillPrice), float(event_order.OrderFee))

            else:
                self.Log("????: {0} at FILL PRICE: {1}".format(ticket, event_order.FillPrice))

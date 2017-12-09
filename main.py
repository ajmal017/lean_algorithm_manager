"""
MD5: fa57b5b10d3a9b645577cc8b5956b8fb
"""

from market import Broker
from alg1 import Algorithm1

# pylint: disable=C0111,W0201,C0413
class WrapperAlgorithm(QCAlgorithm):
    def Initialize(self):
        # Backtest only.
        self.SetCash(100000)
        self.SetStartDate(2017, 1, 1)
        self.SetEndDate(2017, 1, 5)

        self.broker = Broker(parent=self, cash=100000)
        self.algorithms = []
        self.algorithms.append(Algorithm1(parent=self, broker=self.broker,
                                          cash=10000, name="Algorithm1"))


    def __pre(self):
        pass

    def __post(self):
        self.broker.executeOrders()

    def CoarseSelectionFunction(self, coarse):
        symbols = []
        for alg in self.algorithms:
            symbols.extend(alg.CoarseSelectionFunction(coarse))
        return symbols

    def FineSelectionFunction(self, fine):
        symbols = []
        for alg in self.algorithms:
            symbols.extend(alg.FineSelectionFunction(fine))
        return symbols

    def OnData(self, data):
        self.__pre()
        for alg in self.algorithms:
            alg.OnData(data)
        self.__post()

    def OnDividend(self):
        self.__pre()
        for alg in self.algorithms:
            alg.OnDividend()
        self.__post()

    def OnEndOfDay(self):
        self.__pre()
        for alg in self.algorithms:
            alg.OnEndOfDay()
        self.__post()

    def OnEndOfAlgorithm(self):
        self.__pre()
        for alg in self.algorithms:
            alg.OnEndOfAlgorithm()
        self.__post()

    def OnSecuritiesChanged(self, changes):
        self.__pre()
        for alg in self.algorithms:
            # Only call if there's a relevant security in alg
            alg.OnSecuritiesChanged(changes)
        self.__post()

    def OnOrderEvent(self, event_order):
        if event_order.Status == OrderStatus.Submitted:
            self.Debug("SUBMITTED: {0}".format(self.Transactions.GetOrderById(event_order.OrderId)))
        elif event_order.Status == OrderStatus.Filled:
            self.Debug("FILLED: {0} at FILL PRICE: {1}".format(self.Transactions.GetOrderById(event_order.OrderId), event_order.FillPrice))
        else:
            self.Debug(event_order.ToString())
            self.Debug("TICKET: {0}".format(self.tickets[-1]))

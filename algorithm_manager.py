"""
MD5: 00398601971e9e90de7fd258fafdf8f9
"""

# pylint: disable=C0321,C0111,W0201,C0413
try: QCAlgorithm
except NameError: from mocked import *  # pylint: disable=W0614,W0401

from market import Singleton
from decorators import accepts

class AlgorithmManager(QCAlgorithm):

    @accepts(self=object, algorithms=list, benchmarks=list)
    def registerAlgorithms(self, algorithms, benchmarks):
        Singleton.QCAlgorithm = self
        self._warm_up_period = 0
        self._algorithms = algorithms
        self._benchmarks = benchmarks

        plot = Chart('Performance')
        for i in algorithms + benchmarks:
            plot.AddSeries(Series(i.Name, SeriesType.Line, 0, '%'))
        self.AddChart(plot)

    def Log(self, message):
        Singleton.UpdateTime()
        super(AlgorithmManager, self).Log(message)

    def Debug(self, message):
        Singleton.UpdateTime()
        super(AlgorithmManager, self).Debug(message)

    def Error(self, message):
        Singleton.UpdateTime()
        super(AlgorithmManager, self).Error(message)

    def _pre(self):
        pass

    def _post(self):
        for alg in self._algorithms:
            alg.ExecuteOrders()

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

    @accepts(self=object, order_event=OrderEvent)
    def OnOrderEvent(self, order_event):
        if order_event.Status not in [OrderStatus.Submitted, OrderStatus.New]:
            self.Log("OnOrderEvent (1)")
            for alg in self._algorithms:
                self.Log("OnOrderEvent (2...)")
                if alg.TryToFillOnOrderEvent(order_event):
                    self.Log("OnOrderEvent (3)")
                    return
            self.Debug("Could not find matching order")

"""
MD5: c614a780bc6c81bc30f04767f6b26339
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
        self._algorithms = algorithms
        self._benchmarks = benchmarks
        self._warm_up = None
        self._warm_up_from_algorithm = False

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

    def pre(self):
        pass

    def post(self):
        for alg in self._algorithms:
            alg.post()

    def _set_warm_up(self, period):
        self._warm_up = period
        super(AlgorithmManager, self).SetWarmUp(period)

    def SetWarmUp(self, period):
        if not self._warm_up_from_algorithm:
            self._set_warm_up(period)

    def SetWarmUpFromAlgorithm(self, period):
        self._warm_up_from_algorithm = True
        if not self._warm_up or period > self._warm_up:
            self._set_warm_up(period)

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
        self.pre()
        for alg in self._algorithms:
            alg.OnData(data)
        self.post()

    def OnDividend(self):
        if self.IsWarmingUp: return
        self.Log("OnDividend")
        self.pre()
        for alg in self._algorithms:
            alg.OnDividend()
        self.post()

    def OnSecuritiesChanged(self, changes):
        if self.IsWarmingUp: return
        self.Log("OnSecuritiesChanged {0}".format(changes))
        self.pre()
        for alg in self._algorithms:
            # Only call if there's a relevant stock in alg
            alg.OnSecuritiesChanged(changes)
        self.post()

    def OnEndOfDay(self):
        if self.IsWarmingUp: return
        # self.Log("OnEndOfDay")
        self.pre()
        for alg in self._algorithms:
            alg.OnEndOfDay()
        self.post()
        for i in self._algorithms + self._benchmarks:
            self.Plot('Performance', i.Name, i.Performance)

    def OnEndOfAlgorithm(self):
        self.Log("OnEndOfAlgorithm")
        self.pre()
        for alg in self._algorithms:
            alg.OnEndOfAlgorithm()
        self.post()

    @accepts(self=object, order_event=OrderEvent)
    def OnOrderEvent(self, order_event):
        self.Log("OnOrderEvent {0}".format(OrderEvent))
        if order_event.Status not in [OrderStatus.Submitted, OrderStatus.New]:
            self.Log("OnOrderEvent (1)")
            for alg in self._algorithms:
                self.Log("OnOrderEvent (2...)")
                if alg.TryToFillOnOrderEvent(order_event):
                    self.Log("OnOrderEvent (3)")
                    return
            self.Debug("Could not find matching order")

"""
MD5: 2e2ed4bd9993324cd132c6aca2c1d0ab
"""

# pylint: disable=C0321,C0111,W0201,C0413
try: QCAlgorithm
except NameError: from mocked import *  # pylint: disable=W0614,W0401

import bisect
from datetime import date
from decorators import accepts


class SingletonMeta(type):
    def __getattr__(cls, attr):
        """Delegate to parent."""
        if hasattr(cls.QCAlgorithm, attr):
            return getattr(cls.QCAlgorithm, attr)
        else:
            raise AttributeError(attr)

class Singleton(metaclass=SingletonMeta):
    ERROR = 0
    INFO = 1
    LOG = 2
    DEBUG = 3

    Today = date(1, 1, 1)
    QCAlgorithm = None
    LogLevel = INFO
    _log_level_dates = []
    _warm_up = None
    _warm_up_from_algorithm = False

    @classmethod
    def Setup(cls, parent, log_level=INFO):
        cls.Today = date(1, 1, 1)
        cls.QCAlgorithm = parent
        cls.LogLevel = log_level
        cls._warm_up = None
        cls._warm_up_from_algorithm = False

    @classmethod
    def _update_time(cls):
        if cls.Today != cls.QCAlgorithm.Time.date():
            cls.Today = cls.QCAlgorithm.Time.date()
            cls.QCAlgorithm.Log(" - - - - {} - - - - ".format(cls.Today))

    @classmethod
    def SetStartDateLogLevel(cls, log_level, year, month, day):
        bisect.insort(cls._log_level_dates, (date(year, month, day), log_level))

    @classmethod
    def _can_log(cls, log_level):
        matched_log_level = cls.LogLevel
        for elem in cls._log_level_dates:
            if elem[0] <= cls.Today:
                matched_log_level = elem[1]
            else:
                break
        return log_level <= matched_log_level

    @classmethod
    def Log(cls, message):
        if cls._can_log(cls.LOG):
            cls._update_time()
            cls.QCAlgorithm.Log("L " + message)

    @classmethod
    def Debug(cls, message):
        if cls._can_log(cls.DEBUG):
            cls.QCAlgorithm.Log("D " + message)

    @classmethod
    def Info(cls, message):
        if cls._can_log(cls.INFO):
            cls.QCAlgorithm.Log("I " + message)

    @classmethod
    def Error(cls, message):
        if cls._can_log(cls.ERROR):
            cls.QCAlgorithm.Error("E " + message)

    @classmethod
    def CreateSymbol(cls, ticker):
        return cls.QCAlgorithm.Securities[ticker].Symbol

    @classmethod
    def _set_warm_up(cls, period):
        cls._warm_up = period
        Singleton.QCAlgorithm.SetWarmUp(period)

    @classmethod
    def SetWarmUp(cls, period):
        if not cls._warm_up_from_algorithm:
            cls._set_warm_up(period)

    @classmethod
    def SetWarmUpFromAlgorithm(cls, period):
        cls._warm_up_from_algorithm = True
        if not cls._warm_up or period > cls._warm_up:
            cls._set_warm_up(period)


class AlgorithmManager(QCAlgorithm):

    @accepts(self=object, algorithms=list, benchmarks=list)
    def registerAlgorithms(self, algorithms, benchmarks):
        self._algorithms = algorithms
        self._benchmarks = benchmarks

        plot = Chart('Performance')
        for i in benchmarks + algorithms:
            plot.AddSeries(Series(i.Name, SeriesType.Line, 0, '%'))
        self.AddChart(plot)

    def pre(self):
        pass

    def post(self):
        for alg in self._algorithms:
            alg.post()

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
        # Singleton.Debug("OnData")
        self.pre()
        for alg in self._algorithms:
            alg.OnData(data)
        self.post()

    def OnDividend(self):
        Singleton.Debug("OnDividend")
        self.pre()
        for alg in self._algorithms:
            alg.OnDividend()
        self.post()

    def OnSecuritiesChanged(self, changes):
        Singleton.Debug("OnSecuritiesChanged {0}".format(changes))
        self.pre()
        for alg in self._algorithms:
            # Only call if there's a relevant stock in alg
            alg.OnSecuritiesChanged(changes)
        self.post()

    def OnEndOfDay(self):
        Singleton.Log("OnEndOfDay: {}".format(Singleton.Time))
        self.pre()
        for alg in self._algorithms:
            alg.OnEndOfDay()
        self.post()
        for i in self._algorithms + self._benchmarks:
            self.Plot('Performance', i.Name, i.Performance)

    def OnEndOfAlgorithm(self):
        self.pre()
        for alg in self._algorithms:
            alg.OnEndOfAlgorithm()
        self.post()

    @accepts(self=object, order_event=OrderEvent)
    def OnOrderEvent(self, order_event):
        Singleton.Debug("OnOrderEvent {0}".format(OrderEvent))
        if order_event.Status not in [OrderStatus.Submitted, OrderStatus.New]:
            Singleton.Debug("OnOrderEvent (1)")
            for alg in self._algorithms:
                Singleton.Debug("OnOrderEvent (2...)")
                if alg.TryToFillOnOrderEvent(order_event):
                    Singleton.Debug("OnOrderEvent (3)")
                    return
            Singleton.Debug("Could not find matching order")

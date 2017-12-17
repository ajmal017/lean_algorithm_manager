"""
MD5: 660b88c60092252853cd7fa26775e0b3
"""

from algorithm_manager import AlgorithmManager
from market import Broker, BenchmarkSymbol
from alg1 import Algorithm1, Algorithm2, Algorithm3

class MyAlgos(AlgorithmManager):
    def Initialize(self):
        # Backtest only.
        self.SetCash(100000)
        self.SetStartDate(2016, 6, 1)
        self.SetEndDate(2017, 1, 1)

        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Cash)

        self.registerBroker(Broker(self))
        self.registerAlgorithms(
            [Algorithm1(self, broker=self._broker, cash=10000, name="Algorithm1"),
             Algorithm2(self, broker=self._broker, cash=20000, name="Algorithm2"),
             Algorithm3(self, broker=self._broker, cash=30000, name="Algorithm3")],
            [BenchmarkSymbol(parent=self, ticker='SPY'),
             BenchmarkSymbol(parent=self, ticker='VGT')])

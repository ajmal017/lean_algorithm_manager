"""
MD5: 50c06947b2f330f7bfc1bf970e329046
"""

from algorithm_manager import AlgorithmManager
from market import Broker
from alg1 import Algorithm1, Algorithm2, Algorithm3

class MyAlgos(AlgorithmManager):
    def Initialize(self):
        # Backtest only.
        self.SetCash(100000)
        self.SetStartDate(2016, 1, 1)
        self.SetEndDate(2017, 1, 1)

        self.registerBroker(Broker(self))
        self.registerAlgorithms([
            Algorithm1(self, broker=self._broker, cash=10000, name="Algorithm1"),
            Algorithm2(self, broker=self._broker, cash=20000, name="Algorithm2"),
            Algorithm3(self, broker=self._broker, cash=30000, name="Algorithm3")
        ])

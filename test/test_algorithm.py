# pylint: disable=C0111,C0103,C0112
import unittest

from mocked import QCAlgorithm, Securities, Resolution, Symbol
from algorithm import Algorithm
from market import Broker, Position

FOO = Symbol('foo')
BAR = Symbol('bar')
XYZ = Symbol('xyz')

class Algorithm1(Algorithm):
    def Initialize(self):

        # Set the cash we'd like to use for our backtest
        # This is ignored in live trading
        self.SetCash(100000)

        # Start and end dates for the backtest.
        # These are ignored in live trading.
        self.SetStartDate(2016, 1, 1)
        self.SetEndDate(2017, 1, 1)

        # Add assets you'd like to see
        self.Symbol = self.AddEquity("foo", Resolution.Daily).Symbol

class TestAlgorithm(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm()
        self.qc.Securities = Securities([(FOO, 5), (BAR, 50)])
        self.broker = Broker(parent=self.qc, cash=500)
        self.algorithm = Algorithm1(parent=self.qc, broker=self.broker, cash=200, name="alg1")
        self.algorithm.Portfolio[self.algorithm.Symbol] = Position(FOO, 10, 5)

    def test_total_value(self):
        self.assertEqual(self.algorithm.Portfolio.getTotalValue(), 200+(10*5))

if __name__ == '__main__':
    unittest.main()

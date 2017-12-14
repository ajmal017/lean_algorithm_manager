# pylint: disable=C0111,C0103,C0112,W0201
import unittest

from mocked import Securities, Resolution, Symbol
from algorithm import Algorithm
from market import Broker, Position
from algorithm_manager import AlgorithmManager as QCAlgorithm

FOO = Symbol('foo')
BAR = Symbol('bar')
XYZ = Symbol('xyz')

class Algorithm1(Algorithm):
    def Initialize(self):
        self.SetCash(100000)
        self.SetStartDate(2016, 1, 1)
        self.SetEndDate(2017, 1, 1)
        self.stock = self.AddEquity("foo", Resolution.Daily).Symbol


class Algorithm2(Algorithm):
    def Initialize(self):
        self.SetCash(100000)
        self.SetStartDate(2016, 1, 1)
        self.SetEndDate(2017, 1, 1)
        self.stock = self.AddEquity("bar", Resolution.Daily).Symbol


class TestAlgorithm(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm()
        self.qc.Securities = Securities([(FOO, 5), (BAR, 50)])
        self.broker = Broker(self.qc)
        self.broker.Portfolio.Cash = 200

        self.algorithm = Algorithm1(self.qc, broker=self.broker, cash=200, name="alg1")
        self.algorithm.Portfolio[self.algorithm.stock] = Position(FOO, 10, 5)

    def test_algorithms_cash(self):
        self.assertEqual(self.broker.Portfolio.Cash, 200)
        self.assertEqual(self.algorithm.Portfolio.Cash, 200)

    def test_algorithm_total_value(self):
        self.assertEqual(self.algorithm.Portfolio.getTotalValue(), 200+(10*5))

    def test_algorithm_cash_initialization(self):
        alg = Algorithm1(self.qc, broker=self.broker, cash=200, name="alg1")


class TestMultipleAlgorithms(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm()
        self.qc.Securities = Securities([(FOO, 5), (BAR, 50)])
        self.broker = Broker(self.qc)
        self.broker.Portfolio.Cash = 200

        self.algorithm1 = Algorithm1(self.qc, broker=self.broker, cash=200, name="alg1")
        self.algorithm1.Portfolio[self.algorithm1.stock] = Position(FOO, 10, 5)

        self.algorithm2 = Algorithm2(self.qc, broker=self.broker, cash=200, name="alg2")
        self.algorithm2.Portfolio[self.algorithm2.stock] = Position(BAR, 3, 50)

    def test_algorithms_cash(self):
        self.assertEqual(self.algorithm1.Portfolio.Cash, 200)
        self.assertEqual(self.algorithm2.Portfolio.Cash, 200)

    def test_algorithms_total_value(self):
        self.assertEqual(self.algorithm1.Portfolio.getTotalValue(), 200 + (10 * 5))
        self.assertEqual(self.algorithm2.Portfolio.getTotalValue(), 200 + (3 * 50))

    def test_set_warmup(self):
        self.algorithm1.SetWarmUp(123)
        self.algorithm2.SetWarmUp(321)
        self.assertEqual(self.qc.WarmUp, 321)


if __name__ == '__main__':
    unittest.main()

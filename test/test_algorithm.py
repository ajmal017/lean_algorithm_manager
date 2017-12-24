# pylint: disable=C0111,C0103,C0112,W0201,W0212
import unittest

from mocked import Resolution, Symbol, InternalSecurityManager
from algorithm import Algorithm, SimpleAlgorithm
from market import Singleton, Broker, Position
from algorithm_manager import AlgorithmManager as QCAlgorithm

FOO = Symbol('foo')
BAR = Symbol('bar')
XYZ = Symbol('xyz')

class Algorithm1(Algorithm):
    def __init__(self, broker, cash, name="alg1"):
        super(Algorithm1, self).__init__(broker=broker, cash=cash, name=name)

    def Initialize(self):
        self.SetCash(100000)
        self.SetStartDate(2016, 1, 1)
        self.SetEndDate(2017, 1, 1)
        self.stock = self.AddEquity(FOO, Resolution.Daily).Symbol


class Algorithm2(Algorithm):
    def Initialize(self):
        self.SetCash(100000)
        self.SetStartDate(2016, 1, 1)
        self.SetEndDate(2017, 1, 1)
        self.stock = self.AddEquity("bar", Resolution.Daily).Symbol


class TestAlgorithm(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm()
        Singleton.Setup(self.qc)
        self.qc.Securities = InternalSecurityManager([(FOO, 5), (BAR, 50)])
        self.broker = Broker()
        self.broker.Portfolio.CashBook = 200

        self.algorithm = Algorithm1(broker=self.broker, cash=200, name="alg1")
        self.algorithm.Portfolio[self.algorithm.stock] = Position(FOO, 10, 5)

    def test_algorithms_cash(self):
        self.assertEqual(self.broker.Portfolio.CashBook, 200)
        self.assertEqual(self.algorithm.Portfolio.CashBook, 200)

    def test_algorithm_total_value(self):
        self.assertEqual(self.algorithm.Portfolio.TotalPortfolioValue, 200+(10*5))


class TestMultipleAlgorithms(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm()
        Singleton.Setup(self.qc)
        self.qc.Initialize()
        self.qc.Securities = InternalSecurityManager([(FOO, 5), (BAR, 50)])
        self.broker = Broker()
        self.broker.Portfolio.CashBook = 200

        self.algorithm1 = Algorithm1(broker=self.broker, cash=200, name="alg1")
        self.algorithm1.Portfolio[self.algorithm1.stock] = Position(FOO, 10, 5)

        self.algorithm2 = Algorithm2(broker=self.broker, cash=200, name="alg2")
        self.algorithm2.Portfolio[self.algorithm2.stock] = Position(BAR, 3, 50)

    def test_algorithms_cash(self):
        self.assertEqual(self.algorithm1.Portfolio.CashBook, 200)
        self.assertEqual(self.algorithm2.Portfolio.CashBook, 200)
        self.assertEqual(self.algorithm2.Performance, 75.0)

    def test_algorithms_total_value(self):
        self.assertEqual(self.algorithm1.Portfolio.TotalPortfolioValue, 200 + (10 * 5))
        self.assertEqual(self.algorithm2.Portfolio.TotalPortfolioValue, 200 + (3 * 50))

    def test_set_warmup(self):
        self.algorithm1.SetWarmUp(123)
        self.algorithm2.SetWarmUp(321)
        # pylint: disable=E1101
        self.assertEqual(self.qc._warm_up_period, 321)

class TestSimpleAlgorithm(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm()
        Singleton.Setup(self.qc)
        self.qc.Securities = InternalSecurityManager([(FOO, 5), (BAR, 50)])
        self.broker = Broker()
        self.qc.Initialize()
        self.algorithm = Algorithm1(broker=self.broker, cash=200, name="alg1")

    def test_algorithms_cash(self):
        self.algorithm.SetHoldings(FOO, 0.5)
        self.algorithm.SetHoldings('foo', 0.5)



if __name__ == '__main__':
    unittest.main()

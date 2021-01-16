# pylint: disable=C0111,C0103,C0112,W0201,W0212
import unittest

from mocked import Resolution, Symbol, InternalSecurityManager
from market import Position
from singleton import Singleton
from algorithm import Algorithm, AlgorithmManager as QCAlgorithm

FOO = Symbol('foo')
BAR = Symbol('bar')
XYZ = Symbol('xyz')

class TestSimpleAlgorithm(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm()
        Singleton.Setup(self.qc)
        self.qc.Initialize()
        self.qc.Securities = InternalSecurityManager([(FOO, 5), (BAR, 50)])

        self.algorithm1 = Algorithm(name="alg1", allocation=1.0)
        foo = self.algorithm1.AddEquity(FOO, Resolution.Daily).Symbol
        bar = self.algorithm1.AddEquity(BAR, Resolution.Daily).Symbol
        self.algorithm1.Portfolio.SetCash(200)
        self.algorithm1.Portfolio[foo] = Position(FOO, 10, 5)
        self.algorithm1.Portfolio[bar] = Position(BAR, 3, 50)

    def test_set_up(self):
        cash = 200
        foo_value = 10 * 5
        bar_value = 3 * 50
        total_value = 400
        self.assertEqual(self.algorithm1.Portfolio.Cash, cash)
        self.assertEqual(self.algorithm1.Portfolio.TotalHoldingsValue, foo_value + bar_value)
        self.assertEqual(self.algorithm1.Portfolio.TotalPortfolioValue, total_value)

class TestMultipleAlgorithms(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm()
        Singleton.Setup(self.qc)
        self.qc.Initialize()
        self.qc.Securities = InternalSecurityManager([(FOO, 5), (BAR, 50)])
        foo = self.qc.AddEquity(FOO, Resolution.Daily).Symbol
        bar = self.qc.AddEquity(BAR, Resolution.Daily).Symbol

        self.algorithm1 = Algorithm(name="alg1", allocation=0.5)
        self.algorithm1.Portfolio.SetCash(200)
        self.algorithm1.Portfolio[foo] = Position(FOO, 10, 5)

        self.algorithm2 = Algorithm(name="alg2", allocation=0.5)
        self.algorithm2.Portfolio.SetCash(200)
        self.algorithm2.Portfolio[bar] = Position(BAR, 3, 50)

    def test_algorithms_cash(self):
        self.assertEqual(self.algorithm1.Portfolio.Cash, 200)
        self.assertEqual(self.algorithm2.Portfolio.Cash, 200)
        self.assertEqual(self.algorithm2.Portfolio.Performance, 75.0)
        self.assertEqual(self.algorithm2.Performance, 75.0)

    def test_algorithms_total_value(self):
        self.assertEqual(self.algorithm1.Portfolio.TotalPortfolioValue, 200 + (10 * 5))
        self.assertEqual(self.algorithm2.Portfolio.TotalPortfolioValue, 200 + (3 * 50))

    def test_algorithm_set_warmup(self):
        self.algorithm1.SetWarmUp(123)
        self.algorithm2.SetWarmUp(321)
        # pylint: disable=E1101
        self.assertEqual(Singleton._warm_up, 321)

    def test_qc_set_warmup_should_not_override_algorithm(self):
        self.algorithm1.SetWarmUp(123)
        self.algorithm2.SetWarmUp(321)
        Singleton.SetWarmUp(444)
        self.assertEqual(Singleton._warm_up, 321)

    def test_qc_set_warmup_from_main(self):
        Singleton.SetWarmUp(444)
        self.assertEqual(Singleton._warm_up, 444)



if __name__ == '__main__':
    unittest.main()

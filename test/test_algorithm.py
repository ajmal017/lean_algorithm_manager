# pylint: disable=C0111,C0103,C0112,W0201,W0212
import unittest

from datetime import date
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

    def test_algorithm_set_warmup(self):
        self.algorithm1.SetWarmUp(123)
        self.algorithm2.SetWarmUp(321)
        # pylint: disable=E1101
        self.assertEqual(self.qc._warm_up, 321)

    def test_algorithm_set_start_date(self):
        self.algorithm1.SetStartDate(2025, 12, 1)
        self.algorithm2.SetStartDate(1931, 10, 5)
        self.assertEqual(self.qc._start_date, date(1931, 10, 5))

    def test_algorithm_set_end_date(self):
        self.algorithm1.SetEndDate(1931, 10, 5)
        self.algorithm2.SetEndDate(2025, 12, 1)
        self.assertEqual(self.qc._end_date, date(2025, 12, 1))

    def test_qc_set_warmup_should_not_override_algorithm(self):
        self.algorithm1.SetWarmUp(123)
        self.algorithm2.SetWarmUp(321)
        self.qc.SetWarmUp(444)
        self.assertEqual(self.qc._warm_up, 321)

    def test_qc_set_warmup_from_main(self):
        self.qc.SetWarmUp(444)
        self.assertEqual(self.qc._warm_up, 444)

    def test_qc_set_start_date_overrides_algorithm(self):
        self.algorithm1.SetStartDate(2025, 12, 1)
        self.algorithm2.SetStartDate(1931, 10, 5)
        self.qc.SetStartDate(2020, 10, 1)
        self.assertEqual(self.qc._start_date, date(2020, 10, 1))

    def test_qc_set_end_date_overrides_algorithm(self):
        self.algorithm1.SetEndDate(1931, 10, 5)
        self.algorithm2.SetEndDate(2025, 12, 1)
        self.qc.SetEndDate(2020, 10, 1)
        self.assertEqual(self.qc._end_date, date(2020, 10, 1))


class TestSimpleAlgorithm(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm()
        Singleton.Setup(self.qc)
        self.qc.Securities = InternalSecurityManager([(FOO, 5), (BAR, 50)])
        self.broker = Broker()
        self.broker.Portfolio.CashBook = 200
        self.qc.Initialize()
        self.algorithm = Algorithm1(broker=self.broker, cash=150, name="alg1")
        self.algorithm.Portfolio[self.algorithm.stock] = Position(FOO, 10, 5)

    def test_set_holdings_for_new_security(self):
        self.algorithm.SetHoldings(BAR, 0.5)
        self.assertEqual(len(self.broker._to_submit), 1)
        self.assertEqual(self.broker._to_submit[0].Symbol, BAR)
        self.assertEqual(self.broker._to_submit[0].Quantity, 2) # rounded from 2.5

    def test_set_holdings_for_new_security_100(self):
        self.algorithm.SetHoldings(BAR, 1.0)
        self.assertEqual(len(self.broker._to_submit), 1)
        self.assertEqual(self.broker._to_submit[0].Symbol, BAR)
        self.assertEqual(self.broker._to_submit[0].Quantity, 4)

    def test_set_holdings_for_new_security_100_with_liquidate(self):
        self.algorithm.SetHoldings(BAR, 1.0, liquidateExistingHoldings=True)
        self.assertEqual(len(self.broker._to_submit), 2)
        self.assertEqual(self.broker._to_submit[0].Symbol, FOO)
        self.assertEqual(self.broker._to_submit[0].Quantity, -10)
        self.assertEqual(self.broker._to_submit[1].Symbol, BAR)
        self.assertEqual(self.broker._to_submit[1].Quantity, 4)

    def test_set_holdings_for_new_security_0(self):
        self.algorithm.SetHoldings(BAR, 0.0)
        self.assertEqual(len(self.broker._to_submit), 0)

    def test_set_holdings_for_new_security_0_with_liquidate(self):
        self.algorithm.SetHoldings(BAR, 0.0, liquidateExistingHoldings=True)
        self.assertEqual(len(self.broker._to_submit), 1)
        self.assertEqual(self.broker._to_submit[0].Symbol, FOO)
        self.assertEqual(self.broker._to_submit[0].Quantity, -10)

    def test_set_holdings_for_existing_security(self):
        self.algorithm.SetHoldings(FOO, 0.5)
        self.assertEqual(len(self.broker._to_submit), 1)
        self.assertEqual(self.broker._to_submit[0].Symbol, FOO)
        self.assertEqual(self.broker._to_submit[0].Quantity, 10)

    def test_set_holdings_for_existing_security_triggers_sell(self):
        self.algorithm.SetHoldings(FOO, 0.1) # total 4 positions
        self.assertEqual(len(self.broker._to_submit), 1)
        self.assertEqual(self.broker._to_submit[0].Symbol, FOO)
        self.assertEqual(self.broker._to_submit[0].Quantity, -6)

    def test_set_holdings_for_existing_security_100(self):
        self.algorithm.SetHoldings(FOO, 1.0)
        self.assertEqual(len(self.broker._to_submit), 1)
        self.assertEqual(self.broker._to_submit[0].Symbol, FOO)
        self.assertEqual(self.broker._to_submit[0].Quantity, 30)

    def test_set_holdings_for_existing_security_100_with_liquidate(self):
        self.algorithm.SetHoldings(FOO, 1.0, liquidateExistingHoldings=True)
        self.assertEqual(len(self.broker._to_submit), 1)
        self.assertEqual(self.broker._to_submit[0].Symbol, FOO)
        self.assertEqual(self.broker._to_submit[0].Quantity, 30)



if __name__ == '__main__':
    unittest.main()

# pylint: disable=C0111,C0103,C0413
import unittest
import math
from unittest.mock import Mock

# from math import isclose

from mocked import QCAlgorithm, Resolution, Security, Symbol, OrderStatus, InternalSecurityManager, OrderEvent
from market import Portfolio, Position, Broker, InternalOrder, OrderType, CashBook, Cash
from algorithm import Algorithm
from singleton import Singleton

FOO = Symbol('foo')
BAR = Symbol('bar')
XYZ = Symbol('xyz')
USD = Symbol('USD')
BTCUSD = Symbol('BTCUSD')


def SetupSingleton(securities=None, brokerage_portfolio=None, default_order_status=OrderStatus.Submitted):
    qc = QCAlgorithm(default_order_status=default_order_status)
    if securities is not None:
        qc.Securities = InternalSecurityManager(securities)

    if brokerage_portfolio is not None:
        qc.Portfolio = brokerage_portfolio

    Singleton.Setup(qc, broker=Broker())

def MockOrderStatus(broker, status, order=None, quantity=None):
    if order is None:
        for o in list(broker._submitted.values()):
            MockOrderStatus(broker, status, order=o)
        return

    ticket = Singleton.QCAlgorithm.Transactions[order.Ticket.OrderId]
    assert ticket == order.Ticket
    ticket.Status = status

    symbol = ticket.Symbol
    price = Singleton.QCAlgorithm.Securities[symbol].Price
    qty = quantity if quantity else order.Quantity

    order_event = OrderEvent(order.Ticket.OrderId, order.Symbol, qty, price, status=status)

    ticket.OrderEvents.append(order_event)

    Singleton.Broker._submitted.pop(order_event.OrderId)
    order.Portfolio.ProcessFill(order_event, order)
    # Singleton.QCAlgorithm.OnOrderEvent(order_event)


class TestPortfolioWithSinglePosition(unittest.TestCase):
    def setUp(self):
        SetupSingleton(securities=[(FOO, 2.5), (BAR, 10)], default_order_status=OrderStatus.Filled)
        self.portfolio = Portfolio(cash=Cash('USD', 270, 1.0))
        self.portfolio[FOO] = Position(FOO, 12, 2.5)

    def test_total_value(self):
        self.assertEqual(self.portfolio.TotalPortfolioValue, 300)
        Singleton.QCAlgorithm.Securities['foo'] = Security(FOO, price=3)
        self.assertEqual(self.portfolio.TotalPortfolioValue, 306)

    def test_buy_existing_position(self):
        self.portfolio._fill_order(FOO, 1.0, 9.0)
        self.assertEqual(self.portfolio['foo'].Quantity, 13)
        self.assertEqual(self.portfolio['foo'].AveragePrice, 3)
        self.assertEqual(self.portfolio.Cash, 261)

    def test_sell_existing_position(self):
        self.portfolio._fill_order(FOO, -1.0, 3.0)
        self.assertEqual(self.portfolio[FOO].Quantity, 11)
        self.assertEqual(self.portfolio[FOO].AveragePrice, 2.5)
        self.assertEqual(self.portfolio.Cash, 273)


class TestPortfolioWithMultiplePositions(unittest.TestCase):
    def setUp(self):
        SetupSingleton(securities=[(FOO, 2.5), (BAR, 50)], default_order_status=OrderStatus.Filled)
        self.portfolio = Portfolio(cash=Cash('USD', 270, 1.0))
        self.portfolio[FOO] = Position(FOO, 12, 2.5) # 30
        self.portfolio[BAR] = Position(BAR, 2, 50) # 100

    def test_total_value(self):
        self.assertEqual(self.portfolio.TotalPortfolioValue, 400)

    def test_buy_new_position(self):
        abc = Symbol('abc')
        self.portfolio._fill_order(abc, 10.0, 20.0)
        self.assertEqual(len(self.portfolio), 3)
        self.assertEqual(self.portfolio[abc].Quantity, 10)
        self.assertEqual(self.portfolio.Cash, 70)

    def test_buy_existing_position_with_different_price(self):
        self.portfolio._fill_order(BAR, 1.0, 200.0)
        self.assertEqual(len(self.portfolio), 2)
        self.assertEqual(self.portfolio.Cash, 70)
        self.assertEqual(self.portfolio[BAR].Quantity, 3)
        self.assertEqual(self.portfolio[BAR].AveragePrice, 100)

    def test_sell_existing_position(self):
        self.portfolio._fill_order(FOO, -5.0, 4.0)
        self.assertEqual(len(self.portfolio), 2)
        self.assertEqual(self.portfolio.Cash, 290)
        self.assertEqual(self.portfolio[FOO].Quantity, 7)

    def test_sell_existing_position_with_different_price(self):
        self.portfolio._fill_order(BAR, -1.0, 100.0)
        self.assertEqual(len(self.portfolio), 2)
        self.assertEqual(self.portfolio.Cash, 370)
        self.assertEqual(self.portfolio[BAR].Quantity, 1)
        self.assertEqual(self.portfolio[BAR].AveragePrice, 50)

    def test_sell_entire_position(self):
        self.portfolio._fill_order(FOO, -12.0, 4.0)
        self.assertEqual(len(self.portfolio), 2)
        self.assertEqual(self.portfolio.Cash, 318)


class TestHelpers(unittest.TestCase):
    def assert_portfolio(self, portfolio, cash, args):
        # self.assertTrue(isclose(portfolio.Cash, cash))
        if cash is not None:
            self.assertEquals(portfolio.Cash, cash)
        portfolio_dict = {sec: pos.Quantity for sec, pos in portfolio.items() if pos.Quantity > 0}
        args_dict = {sec: qty for sec, qty in args.items() if qty > 0}
        self.assertDictEqual(portfolio_dict, args_dict)
        # for symb, qty in iter(args.items()):
        #     self.assertEqual(portfolio[symb].Quantity, qty)

    def assert_portfolio_cashbook(self, portfolio, args):
        portfolio_dict = {sec: cash.Amount for sec, cash in portfolio.CashBook.items() if cash.Amount > 0}
        args_dict = {sec: qty for sec, qty in args.items() if qty > 0}
        self.assertDictEqual(portfolio_dict, args_dict)
        # for symb, qty in iter(args.items()):
        #     self.assertEqual(portfolio[symb].Quantity, qty)

    def assert_order(self, order, args):
        self.assert_orders({0: order}, args)

    def assert_orders(self, transactions, args):
        orders = [(x.Symbol, x.Quantity, x.OrderType) for x in transactions.values()]
        expected_orders = [(symb, qty, OrderType.Market) for symb, qty in args.items()]
        self.assertEqual(orders, expected_orders)


class TestMarketOrders(TestHelpers):
    def setUp(self):
        SetupSingleton(brokerage_portfolio=Portfolio(cash=Cash('USD', 200.0, 1.0)),
                       securities=[(FOO, 1), (BAR, 10), (XYZ, 100)])

        self.portfolio = Portfolio(cash=Cash('USD', 200, 1.0))

    def test_set_up(self):
        self.assert_portfolio(self.portfolio, 200, {FOO: 0, BAR: 0, XYZ: 0})

        # Remaining orders that are submitted to real broker.
        self.assertEqual(len(Singleton.QCAlgorithm.Transactions), 0)

    def test_buying(self):
        order = InternalOrder(self.portfolio, XYZ, 1, order_type=OrderType.Market)

        # Adding and executing order.
        Singleton.Broker.ExecuteOrder(order)
        self.assert_portfolio(self.portfolio, 200, {FOO:0, BAR:0, XYZ:0})
        self.assert_orders(Singleton.QCAlgorithm.Transactions, {XYZ:1})
        self.assert_orders(Singleton.Broker._submitted, {XYZ:1})

        # Fill order.
        MockOrderStatus(Singleton.Broker, OrderStatus.Filled, order)
        self.assert_orders(Singleton.Broker._submitted, {})
        self.assert_portfolio(self.portfolio, 100, {FOO:0, BAR:0, XYZ:1})


class TestImportFromBroker(TestHelpers):
    def test_securities(self):
        brokerage_portfolio = Portfolio(cash=Cash('USD', 200.0, 1.0))
        brokerage_portfolio.CashBook['USD'] = Cash('USD', 200.0, 1.0)
        brokerage_portfolio[BAR] = Position(BAR, 3, 50)

        SetupSingleton(brokerage_portfolio=brokerage_portfolio,
                       securities=[(FOO, 1), (BAR, 10), (XYZ, 100)])

        Singleton.Broker.ImportFromBroker()
        self.assert_portfolio(Singleton.QCAlgorithm.Portfolio, 200, {BAR: 3})
        self.assert_portfolio(Singleton.Broker.Portfolio, 200, {BAR: 3})

    def test_crypto(self):
        brokerage_portfolio = Portfolio(cash=Cash('USD', 200.0, 1.0))
        brokerage_portfolio.CashBook['USD'] = Cash('USD', 200.0, 1.0)
        brokerage_portfolio.CashBook['BTC'] = Cash('BTC', 0.123, 55_000)

        SetupSingleton(brokerage_portfolio=brokerage_portfolio,
                       securities=[(USD, 1), (BTCUSD, 55_000)])

        self.assert_portfolio_cashbook(Singleton.QCAlgorithm.Portfolio, {'USD': 200, 'BTC': 0.123})

        Singleton.Broker.ImportFromBroker()
        self.assert_portfolio(Singleton.Broker.Portfolio, 200, {BTCUSD: 0.123})

class TestBrokerPortfolio(TestHelpers):
    def setUp(self):
        brokerage_portfolio = Portfolio(cash=Cash('USD', 100.0, 1.0))
        brokerage_portfolio.CashBook['USD'] = Cash('USD', 100.0, 1.0)

        SetupSingleton(brokerage_portfolio=brokerage_portfolio,
                       securities=[(FOO, 1), (BAR, 10), (XYZ, 100)])
        brokerage_portfolio[BAR] = Position(BAR, 3, 50)
        Singleton.Broker.ImportFromBroker()

        self.algorithm1 = Algorithm(name="alg1")
        self.algorithm1.Portfolio.SetCash(200)
        self.algorithm1.Portfolio[FOO] = Position(FOO, 10, 5)

    def test_set_up(self):
        self.assert_portfolio(Singleton.Broker.Portfolio, 100, {FOO: 0, BAR: 3, XYZ: 0})
        self.assert_portfolio(self.algorithm1.Portfolio, 200, {FOO: 10, BAR: 0, XYZ: 0})

        # Remaining orders that are submitted to real broker.
        self.assertEqual(len(Singleton.QCAlgorithm.Transactions), 0)

    def test_buying_asset_that_was_not_imported(self):
        order = InternalOrder(self.algorithm1.Portfolio, XYZ, 1, order_type=OrderType.Market)

        # Adding and executing order.
        Singleton.Broker.ExecuteOrder(order)
        self.assert_portfolio(self.algorithm1.Portfolio, 200, {FOO:10, BAR:0, XYZ:0})
        self.assert_orders(Singleton.QCAlgorithm.Transactions, {XYZ:1})
        self.assert_orders(Singleton.Broker._submitted, {XYZ:1})

        # Fill order.
        MockOrderStatus(Singleton.Broker, OrderStatus.Filled, order)
        self.assert_orders(Singleton.Broker._submitted, {})
        self.assert_portfolio(Singleton.Broker.Portfolio, 100, {FOO: 0, BAR: 3, XYZ: 0})
        self.assert_portfolio(self.algorithm1.Portfolio, 100, {FOO:10, BAR:0, XYZ:1})


    def test_buying_partial_position_of_asset_that_was_imported(self):
        order = InternalOrder(self.algorithm1.Portfolio, BAR, 1, order_type=OrderType.Market)

        # Adding and executing order.
        Singleton.Broker.ExecuteOrder(order)
        self.assert_portfolio(Singleton.Broker.Portfolio, 100+10, {FOO: 0, BAR: 2, XYZ: 0})
        self.assert_portfolio(self.algorithm1.Portfolio, 200-10, {FOO:10, BAR:1, XYZ:0})
        self.assert_orders(Singleton.QCAlgorithm.Transactions, {})
        self.assert_orders(Singleton.Broker._submitted, {})


    def test_buying_larger_position_of_asset_that_was_imported(self):
        order = InternalOrder(self.algorithm1.Portfolio, BAR, 4, order_type=OrderType.Market)

        # Adding and executing order.
        Singleton.Broker.ExecuteOrder(order)
        self.assert_portfolio(Singleton.Broker.Portfolio, 100+30, {FOO: 0, BAR: 0, XYZ: 0})
        self.assert_portfolio(self.algorithm1.Portfolio, 200-30, {FOO:10, BAR:3, XYZ:0})
        self.assert_orders(Singleton.QCAlgorithm.Transactions, {BAR:1})
        self.assert_orders(Singleton.Broker._submitted, {BAR:1})

        # Fill order.
        MockOrderStatus(Singleton.Broker, OrderStatus.Filled, order)
        self.assert_orders(Singleton.Broker._submitted, {})
        self.assert_portfolio(Singleton.Broker.Portfolio, 100+30, {FOO: 0, BAR: 0, XYZ: 0})
        self.assert_portfolio(self.algorithm1.Portfolio, 200-30-10, {FOO:10, BAR:4, XYZ:0})

    def test_buying_asset_but_need_to_sell_imported_assets(self):
        order = InternalOrder(self.algorithm1.Portfolio, XYZ, 2, order_type=OrderType.Market)

        # Adding and executing order.
        Singleton.Broker.ExecuteOrder(order)

        self.assert_orders(Singleton.QCAlgorithm.Transactions, {BAR:-3, XYZ:2})
        self.assert_orders(Singleton.Broker._submitted, {BAR:-3, XYZ:2})

        # Fill order.
        orders = [order for order in Singleton.Broker._submitted.values()]
        for order in orders:
            MockOrderStatus(Singleton.Broker, OrderStatus.Filled, order)
        self.assert_orders(Singleton.Broker._submitted, {})
        self.assert_portfolio(Singleton.Broker.Portfolio, 100+30, {FOO: 0, BAR: 0, XYZ: 0})
        self.assert_portfolio(self.algorithm1.Portfolio, 0, {FOO:10, BAR:0, XYZ:2})

if __name__ == '__main__':
    unittest.main()

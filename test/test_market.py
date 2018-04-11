# pylint: disable=C0111,C0103,C0413
import unittest
import math

from mocked import QCAlgorithm, Security, Symbol, OrderStatus, InternalSecurityManager, OrderEvent
from market import Singleton, Portfolio, Position, Broker, InternalOrder, OrderType


FOO = Symbol('foo')
BAR = Symbol('bar')
XYZ = Symbol('xyz')

def order_qty(orders, symbol):
    for order in orders:
        if order.Symbol == symbol: return order.Quantity
    return None

def MockOrderStatus(broker, status, order=None, quantity=None):
    if order is None:
        for o in list(broker.submitted.values()):
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

    order.Portfolio.Broker.submitted.pop(order_event.OrderId)
    order.Portfolio.ProcessOrderEvent(order_event, order)
    # Singleton.QCAlgorithm.OnOrderEvent(order_event)


class TestEmpyPortfolio(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm()
        self.qc.Securities = InternalSecurityManager([(FOO, 5), (BAR, 50)])
        Singleton.Setup(self.qc)
        self.broker = Broker()
        self.Portfolio = Portfolio(broker=self.broker, cash=100)

    def test_total_value(self):
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 100)

    def test_zero_quantity(self):
        self.assertEqual(self.Portfolio['non existing'].Quantity, 0)

    def test_target_allocation(self):
        order = self.Portfolio.GenerateOrder(FOO, 0.5)
        self.assertEqual(order, InternalOrder(self.Portfolio, FOO, 10.0))

    def test_partial_target_allocation(self):
        order = self.Portfolio.GenerateOrder(FOO, 0.61)
        self.assertEqual(order, InternalOrder(self.Portfolio, FOO, math.floor(12.2)))

    def test_liquidate_all(self):
        self.Portfolio.Liquidate()
        self.broker.executeOrders()
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 100)
        self.assertEqual(self.Portfolio.CashBook, 100)

    def test_liquidate_security(self):
        self.Portfolio.Liquidate(FOO)
        self.broker.executeOrders()
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 100)
        self.assertEqual(self.Portfolio.CashBook, 100)


class TestPortfolioWithSinglePosition(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm(default_order_status=OrderStatus.Filled)
        self.qc.Securities = InternalSecurityManager([(FOO, 2.5), (BAR, 10)])
        Singleton.Setup(self.qc)
        self.broker = Broker()
        self.Portfolio = Portfolio(broker=self.broker, cash=270)
        self.Portfolio[FOO] = Position(FOO, 12, 2.5)

    def test_total_value(self):
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 300)
        self.qc.Securities['foo'] = Security(FOO, price=3)
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 306)

    def test_liquidate_all(self):
        self.Portfolio.Liquidate()
        self.broker.executeOrders()
        MockOrderStatus(self.broker, OrderStatus.Filled)
        profit = 12 * 2.5
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 270 + profit)
        self.assertEqual(self.Portfolio.CashBook, 270 + profit)

    def test_liquidate_security(self):
        self.Portfolio.Liquidate(FOO)
        self.broker.executeOrders()
        MockOrderStatus(self.broker, OrderStatus.Filled)
        profit = 12 * 2.5
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 270 + profit)
        self.assertEqual(self.Portfolio.CashBook, 270 + profit)

    def test_buy_existing_position(self):
        self.Portfolio.FillOrder(FOO, 1, 9.0)
        self.assertEqual(self.Portfolio['foo'].Quantity, 13)
        self.assertEqual(self.Portfolio['foo'].AveragePrice, 3)
        self.assertEqual(self.Portfolio.CashBook, 261)

    def test_sell_existing_position(self):
        self.Portfolio.FillOrder(FOO, -1, 3.0)
        self.assertEqual(self.Portfolio[FOO].Quantity, 11)
        self.assertEqual(self.Portfolio[FOO].AveragePrice, 2.5)
        self.assertEqual(self.Portfolio.CashBook, 273)

    def test_target_allocation_equals_current_allocation(self):
        order = self.Portfolio.GenerateOrder(FOO, 0.1)
        self.assertEqual(order, InternalOrder(self.Portfolio, FOO, 0.0))

    def test_target_allocation(self):
        order = self.Portfolio.GenerateOrder(FOO, 0.2)
        self.assertEqual(order, InternalOrder(self.Portfolio, FOO, 12.0))

    def test_target_deallocation(self):
        order = self.Portfolio.GenerateOrder(FOO, 0.05)
        self.assertEqual(order, InternalOrder(self.Portfolio, FOO, -6.0))

    def test_partial_target_allocation(self):
        order = self.Portfolio.GenerateOrder(FOO, 0.21)
        self.assertEqual(order, InternalOrder(self.Portfolio, FOO, math.floor(13.2)))

    def test_target_allocation_for_nonexisting_position(self):
        order = self.Portfolio.GenerateOrder(BAR, 0.6)
        self.assertEqual(order, InternalOrder(self.Portfolio, BAR, 18.0))


class TestPortfolioWithMultiplePositions(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm(default_order_status=OrderStatus.Filled)
        self.qc.Securities = InternalSecurityManager([(FOO, 2.5), (BAR, 50)])
        Singleton.Setup(self.qc)
        self.broker = Broker()
        self.Portfolio = Portfolio(broker=self.broker, cash=270)
        self.Portfolio[FOO] = Position(FOO, 12, 2.5) # 30
        self.Portfolio[BAR] = Position(BAR, 2, 50) # 100

    def test_total_value(self):
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 400)

    def test_liquidate_all(self):
        self.Portfolio.Liquidate()
        self.broker.executeOrders()
        MockOrderStatus(self.broker, OrderStatus.Filled)
        profit = 12 * 2.5 + 2 * 50
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 270 + profit)
        self.assertEqual(self.Portfolio.CashBook, 270 + profit)

    def test_liquidate_security(self):
        self.Portfolio.Liquidate(FOO)
        self.broker.executeOrders()
        MockOrderStatus(self.broker, OrderStatus.Filled)
        profit = 12 * 2.5
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 270 + 100 + profit)
        self.assertEqual(self.Portfolio.CashBook, 270 + profit)

    def test_buy_new_position(self):
        abc = Symbol('abc')
        self.Portfolio.FillOrder(abc, 10, 20.0)
        self.assertEqual(len(self.Portfolio), 3)
        self.assertEqual(self.Portfolio[abc].Quantity, 10)
        self.assertEqual(self.Portfolio.CashBook, 70)

    def test_buy_existing_position_with_different_price(self):
        self.Portfolio.FillOrder(BAR, 1, 200.0)
        self.assertEqual(len(self.Portfolio), 2)
        self.assertEqual(self.Portfolio.CashBook, 70)
        self.assertEqual(self.Portfolio[BAR].Quantity, 3)
        self.assertEqual(self.Portfolio[BAR].AveragePrice, 100)

    def test_sell_existing_position(self):
        self.Portfolio.FillOrder(FOO, -5, 4.0)
        self.assertEqual(len(self.Portfolio), 2)
        self.assertEqual(self.Portfolio.CashBook, 290)
        self.assertEqual(self.Portfolio[FOO].Quantity, 7)

    def test_sell_existing_position_with_different_price(self):
        self.Portfolio.FillOrder(BAR, -1, 100.0)
        self.assertEqual(len(self.Portfolio), 2)
        self.assertEqual(self.Portfolio.CashBook, 370)
        self.assertEqual(self.Portfolio[BAR].Quantity, 1)
        self.assertEqual(self.Portfolio[BAR].AveragePrice, 50)

    def test_sell_entire_position(self):
        self.Portfolio.FillOrder(FOO, -12, 4.0)
        self.assertEqual(len(self.Portfolio), 1)
        self.assertEqual(self.Portfolio.CashBook, 318)


from algorithm_manager import AlgorithmManager as QCAlgorithm

class TestMarketOrders(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm()
        self.qc.Securities = InternalSecurityManager([(FOO, 1), (BAR, 10), (XYZ, 100)])
        Singleton.Setup(self.qc)
        self.broker = Broker()
        self.broker.Portfolio = Portfolio(broker=self.broker)
        self.broker.Portfolio[FOO] = Position(FOO, 100, 1)
        self.broker.Portfolio[BAR] = Position(BAR, 10, 10)

        self.portfolio = Portfolio(broker=self.broker, cash=200)

    def assert_portfolio(self, portfolio, cash, args):
        self.assertEqual(portfolio.CashBook, cash)
        for symb, qty in iter(args.items()):
            if qty == 0:
                self.assertTrue(symb not in portfolio)
            else:
                self.assertEqual(portfolio[symb].Quantity, qty)

    def assert_orders(self, transactions, args):
        self.assertEqual(len(transactions), len(args))
        orders = [(x.Symbol, x.Quantity, x.OrderType) for x in transactions.values()]
        for symb, qty in iter(args.items()):
            if qty == 0:
                self.assertTrue(symb not in transactions)
            else:
                self.assertTrue((symb, qty, OrderType.Market) in orders)


    def test_initial_state(self):
        self.assert_portfolio(self.broker.Portfolio, 0, {FOO:100, BAR:10, XYZ:0})
        self.assert_portfolio(self.portfolio, 200, {FOO: 0, BAR: 0, XYZ: 0})

        # Remaining orders that are submitted to real broker.
        self.assertEqual(len(self.qc.Transactions), 0)

    def test_buying_existing_stock_in_available_portfolio(self):
        order = InternalOrder(self.portfolio, FOO, 2, order_type=OrderType.Market)

        # Adding and executing order.
        self.broker.AddOrder(order)
        self.broker.executeOrders()
        self.assert_portfolio(self.broker.Portfolio, 0, {FOO: 98, BAR: 10, XYZ: 0})
        self.assert_portfolio(self.portfolio, 198, {FOO: 2, BAR: 0, XYZ: 0})
        self.assert_orders(self.qc.Transactions, {})

    def test_buying_inexisting_stock_in_available_portfolio(self):
        order = InternalOrder(self.portfolio, XYZ, 1, order_type=OrderType.Market)

        # Adding and executing order.
        self.broker.AddOrder(order)
        self.broker.executeOrders()
        self.assert_portfolio(self.broker.Portfolio, 0, {FOO:100, BAR:10, XYZ:0})
        self.assert_portfolio(self.portfolio, 200, {FOO: 0, BAR: 0, XYZ: 0})
        self.assert_orders(self.qc.Transactions, {XYZ:1})
        self.assert_orders(self.broker.submitted, {XYZ: 1})

        # Fill order.
        MockOrderStatus(self.broker, OrderStatus.Filled, order)
        self.assert_orders(self.broker.submitted, {})
        self.assert_portfolio(self.broker.Portfolio, 0, {FOO:100, BAR:10, XYZ:0})
        self.assert_portfolio(self.portfolio, 100, {FOO:0, BAR:0, XYZ:1})


if __name__ == '__main__':
    unittest.main()

# pylint: disable=C0111,C0103,C0413
import unittest

from mocked import QCAlgorithm, Securities, Security, Symbol, OrderStatus
from market import Portfolio, Position, Broker, Order, OrderType


def order_qty(orders, symbol):
    for order in orders:
        if order.Symbol == symbol: return order.Quantity
    return None

FOO = Symbol('foo')
BAR = Symbol('bar')
XYZ = Symbol('xyz')

class TestEmpyPortfolio(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm()
        self.qc.Securities = Securities([(FOO, 5), (BAR, 50)])
        self.broker = Broker(self.qc)
        self.qc.registerBroker(self.broker)
        self.Portfolio = Portfolio(parent=self.qc, broker=self.broker, cash=100)

    def test_total_value(self):
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 100)

    def test_zero_quantity(self):
        self.assertEqual(self.Portfolio['non existing'].Quantity, 0)

    def test_target_allocation(self):
        order = self.Portfolio.GenerateOrder(FOO, 0.5)
        self.assertEqual(order, Order(self.Portfolio, FOO, 10.0))

    def test_partial_target_allocation(self):
        order = self.Portfolio.GenerateOrder(FOO, 0.61)
        self.assertEqual(order, Order(self.Portfolio, FOO, 12.2))

    def test_liquidate_all(self):
        self.Portfolio.Liquidate()
        self.broker.executeOrders()
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 100)
        self.assertEqual(self.Portfolio.Cash, 100)

    def test_liquidate_security(self):
        self.Portfolio.Liquidate(FOO)
        self.broker.executeOrders()
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 100)
        self.assertEqual(self.Portfolio.Cash, 100)


class TestPortfolioWithSinglePosition(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm(default_order_status=OrderStatus.Filled)
        self.qc.Securities = Securities([(FOO, 2.5), (BAR, 10)])
        self.broker = Broker(self.qc)
        self.qc.registerBroker(self.broker)
        self.Portfolio = Portfolio(parent=self.qc, broker=self.broker, cash=270)
        self.Portfolio[FOO] = Position(FOO, 12, 2.5)

    def test_total_value(self):
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 300)
        self.qc.Securities['foo'] = Security(FOO, price=3)
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 306)

    def test_liquidate_all(self):
        self.Portfolio.Liquidate()
        self.broker.executeOrders()
        self.qc.SetOrderStatus(OrderStatus.Filled)
        profit = 12 * 2.5
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 270 + profit)
        self.assertEqual(self.Portfolio.Cash, 270 + profit)

    def test_liquidate_security(self):
        self.Portfolio.Liquidate(FOO)
        self.broker.executeOrders()
        self.qc.SetOrderStatus(OrderStatus.Filled)
        profit = 12 * 2.5
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 270 + profit)
        self.assertEqual(self.Portfolio.Cash, 270 + profit)

    def test_buy_existing_position(self):
        self.Portfolio.FillOrder(FOO, 1, 9)
        self.assertEqual(self.Portfolio[FOO].Quantity, 13)
        self.assertEqual(self.Portfolio[FOO].AveragePrice, 3)
        self.assertEqual(self.Portfolio.Cash, 261)

    def test_sell_existing_position(self):
        self.Portfolio.FillOrder(FOO, -1, 3)
        self.assertEqual(self.Portfolio[FOO].Quantity, 11)
        self.assertEqual(self.Portfolio[FOO].AveragePrice, 2.5)
        self.assertEqual(self.Portfolio.Cash, 273)

    def test_target_allocation_equals_current_allocation(self):
        order = self.Portfolio.GenerateOrder(FOO, 0.1)
        self.assertEqual(order, Order(self.Portfolio, FOO, 0.0))

    def test_target_allocation(self):
        order = self.Portfolio.GenerateOrder(FOO, 0.2)
        self.assertEqual(order, Order(self.Portfolio, FOO, 12.0))

    def test_target_deallocation(self):
        order = self.Portfolio.GenerateOrder(FOO, 0.05)
        self.assertEqual(order, Order(self.Portfolio, FOO, -6.0))

    def test_partial_target_allocation(self):
        order = self.Portfolio.GenerateOrder(FOO, 0.21)
        self.assertEqual(order, Order(self.Portfolio, FOO, 13.2))

    def test_target_allocation_for_nonexisting_position(self):
        order = self.Portfolio.GenerateOrder(BAR, 0.6)
        self.assertEqual(order, Order(self.Portfolio, BAR, 18.0))


class TestPortfolioWithMultiplePositions(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm(default_order_status=OrderStatus.Filled)
        self.qc.Securities = Securities([(FOO, 2.5), (BAR, 50)])
        self.broker = Broker(self.qc)
        self.qc.registerBroker(self.broker)
        self.Portfolio = Portfolio(parent=self.qc, broker=self.broker, cash=270)
        self.Portfolio[FOO] = Position(FOO, 12, 2.5) # 30
        self.Portfolio[BAR] = Position(BAR, 2, 50) # 100

    def test_total_value(self):
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 400)

    def test_liquidate_all(self):
        self.Portfolio.Liquidate()
        self.broker.executeOrders()
        self.qc.SetOrderStatus(OrderStatus.Filled)
        profit = 12 * 2.5 + 2 * 50
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 270 + profit)
        self.assertEqual(self.Portfolio.Cash, 270 + profit)

    def test_liquidate_security(self):
        self.Portfolio.Liquidate(FOO)
        self.broker.executeOrders()
        self.qc.SetOrderStatus(OrderStatus.Filled)
        profit = 12 * 2.5
        self.assertEqual(self.Portfolio.TotalPortfolioValue, 270 + 100 + profit)
        self.assertEqual(self.Portfolio.Cash, 270 + profit)

    def test_buy_new_position(self):
        self.Portfolio.FillOrder('abc', 10, 20)
        self.assertEqual(len(self.Portfolio), 3)
        self.assertEqual(self.Portfolio['abc'].Quantity, 10)
        self.assertEqual(self.Portfolio.Cash, 70)

    def test_buy_existing_position_with_different_price(self):
        self.Portfolio.FillOrder(BAR, 1, 200)
        self.assertEqual(len(self.Portfolio), 2)
        self.assertEqual(self.Portfolio.Cash, 70)
        self.assertEqual(self.Portfolio[BAR].Quantity, 3)
        self.assertEqual(self.Portfolio[BAR].AveragePrice, 100)

    def test_sell_existing_position(self):
        self.Portfolio.FillOrder(FOO, -5, 4)
        self.assertEqual(len(self.Portfolio), 2)
        self.assertEqual(self.Portfolio.Cash, 290)
        self.assertEqual(self.Portfolio[FOO].Quantity, 7)

    def test_sell_existing_position_with_different_price(self):
        self.Portfolio.FillOrder(BAR, -1, 100)
        self.assertEqual(len(self.Portfolio), 2)
        self.assertEqual(self.Portfolio.Cash, 370)
        self.assertEqual(self.Portfolio[BAR].Quantity, 1)
        self.assertEqual(self.Portfolio[BAR].AveragePrice, 50)

    def test_sell_entire_position(self):
        self.Portfolio.FillOrder(FOO, -12, 4)
        self.assertEqual(len(self.Portfolio), 1)
        self.assertEqual(self.Portfolio.Cash, 318)


from algorithm_manager import AlgorithmManager as QCAlgorithm

class TestMarketOrders(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm()
        self.qc.Securities = Securities([(FOO, 1), (BAR, 10), (XYZ, 100)])
        self.broker = Broker(self.qc)
        self.qc.registerBroker(self.broker)
        self.broker.Portfolio.Cash = 0
        self.broker.Portfolio = Portfolio(parent=self.qc, broker=self.broker)
        self.broker.Portfolio[FOO] = Position(FOO, 100, 1)
        self.broker.Portfolio[BAR] = Position(BAR, 10, 10)

        self.portfolio = Portfolio(parent=self.qc, broker=self.broker, cash=200)
        self.qc.registerBroker(self.broker)

    def assert_portfolio(self, portfolio, cash, args):
        self.assertEqual(portfolio.Cash, cash)
        for symb, qty in args.iteritems():
            if qty == 0:
                self.assertTrue(symb not in portfolio)
            else:
                self.assertEqual(portfolio[symb].Quantity, qty)

    def assert_orders(self, transactions, args):
        self.assertEqual(len(transactions), len(args))
        orders = [(x.Symbol, x.Quantity, x.Type) for x in transactions.values()]
        for symb, qty in args.iteritems():
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
        order = Order(self.portfolio, FOO, 2, order_type=OrderType.Market)

        # Adding and executing order.
        self.broker.AddOrder(order)
        self.broker.executeOrders()
        self.assert_portfolio(self.broker.Portfolio, 0, {FOO: 98, BAR: 10, XYZ: 0})
        self.assert_portfolio(self.portfolio, 198, {FOO: 2, BAR: 0, XYZ: 0})
        self.assert_orders(self.qc.Transactions, {})

    def test_buying_inexisting_stock_in_available_portfolio(self):
        order = Order(self.portfolio, XYZ, 1, order_type=OrderType.Market)

        # Adding and executing order.
        self.broker.AddOrder(order)
        self.broker.executeOrders()
        self.assert_portfolio(self.broker.Portfolio, 0, {FOO:100, BAR:10, XYZ:0})
        self.assert_portfolio(self.portfolio, 200, {FOO: 0, BAR: 0, XYZ: 0})
        self.assert_orders(self.qc.Transactions, {XYZ:1})
        self.assert_orders(self.broker.submitted, {XYZ: 1})

        # Fill order.
        self.qc.SetOrderStatus(OrderStatus.Filled, order)
        self.assert_orders(self.broker.submitted, {})
        self.assert_portfolio(self.broker.Portfolio, 0, {FOO:100, BAR:10, XYZ:0})
        self.assert_portfolio(self.portfolio, 100, {FOO:0, BAR:0, XYZ:1})


if __name__ == '__main__':
    unittest.main()

# pylint: disable=C0111,C0103
import unittest

from mocked import QCAlgorithm, Securities, Security, Symbol
from market import Portfolio, Position, Broker, Order, OrderType, OrderStatus


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
        self.assertEqual(self.Portfolio.getTotalValue(), 100)

    def test_get_allocation_for_nonexisting_position(self):
        self.assertEqual(self.Portfolio.getCurrentAllocation(FOO), 0.0)

    def test_target_allocation(self):
        orders = self.Portfolio.getOrdersForTargetAllocation(FOO, 0.5)
        self.assertEqual(len(orders), 1)
        self.assertEqual(order_qty(orders, FOO), 10.0)

    def test_partial_target_allocation(self):
        orders = self.Portfolio.getOrdersForTargetAllocation(FOO, 0.61)
        self.assertEqual(len(orders), 1)
        self.assertEqual(order_qty(orders, FOO), 12.2)

    def test_liquidate_all(self):
        self.Portfolio.Liquidate()
        self.broker.executeOrders()
        self.assertEqual(self.Portfolio.getTotalValue(), 100)
        self.assertEqual(self.Portfolio.Cash, 100)

    def test_liquidate_security(self):
        self.Portfolio.Liquidate(FOO)
        self.broker.executeOrders()
        self.assertEqual(self.Portfolio.getTotalValue(), 100)
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
        self.assertEqual(self.Portfolio.getTotalValue(), 300)
        self.qc.Securities[FOO] = Security(FOO, price=3)
        self.assertEqual(self.Portfolio.getTotalValue(), 306)

    def test_liquidate_all(self):
        self.Portfolio.Liquidate()
        self.broker.executeOrders()
        self.qc.SetOrderStatus(OrderStatus.Filled)
        profit = 12 * 2.5
        self.assertEqual(self.Portfolio.getTotalValue(), 270 + profit)
        self.assertEqual(self.Portfolio.Cash, 270 + profit)

    def test_liquidate_security(self):
        self.Portfolio.Liquidate(FOO)
        self.broker.executeOrders()
        self.qc.SetOrderStatus(OrderStatus.Filled)
        profit = 12 * 2.5
        self.assertEqual(self.Portfolio.getTotalValue(), 270 + profit)
        self.assertEqual(self.Portfolio.Cash, 270 + profit)

    def test_buy_existing_position(self):
        self.Portfolio.fillOrder(FOO, 1, 9)
        self.assertEqual(self.Portfolio[FOO].Quantity, 13)
        self.assertEqual(self.Portfolio[FOO].AveragePrice, 3)
        self.assertEqual(self.Portfolio.Cash, 261)

    def test_sell_existing_position(self):
        self.Portfolio.fillOrder(FOO, -1, 3)
        self.assertEqual(self.Portfolio[FOO].Quantity, 11)
        self.assertEqual(self.Portfolio[FOO].AveragePrice, 2.5)
        self.assertEqual(self.Portfolio.Cash, 273)

    def test_get_allocation_for_existing_position(self):
        self.assertEqual(self.Portfolio.getCurrentAllocation(FOO), 0.1)

    def test_get_allocation_for_nonexisting_position(self):
        self.assertEqual(self.Portfolio.getCurrentAllocation(BAR), 0.0)

    def test_target_allocation_equals_current_allocation(self):
        orders = self.Portfolio.getOrdersForTargetAllocation(FOO, 0.1)
        self.assertEqual(len(orders), 1)
        self.assertEqual(order_qty(orders, FOO), 0.0)

    def test_target_allocation(self):
        orders = self.Portfolio.getOrdersForTargetAllocation(FOO, 0.2)
        self.assertEqual(len(orders), 1)
        self.assertEqual(order_qty(orders, FOO), 12.0)

    def test_target_deallocation(self):
        orders = self.Portfolio.getOrdersForTargetAllocation(FOO, 0.05)
        self.assertEqual(len(orders), 1)
        self.assertEqual(order_qty(orders, FOO), -6.0)

    def test_partial_target_allocation(self):
        orders = self.Portfolio.getOrdersForTargetAllocation(FOO, 0.21)
        self.assertEqual(len(orders), 1)
        self.assertEqual(order_qty(orders, FOO), 13.2)

    def test_target_allocation_for_nonexisting_position(self):
        orders = self.Portfolio.getOrdersForTargetAllocation(BAR, 0.6)
        self.assertEqual(len(orders), 1)
        self.assertEqual(order_qty(orders, BAR), 18.0)


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
        self.assertEqual(self.Portfolio.getTotalValue(), 400)

    def test_liquidate_all(self):
        self.Portfolio.Liquidate()
        self.broker.executeOrders()
        self.qc.SetOrderStatus(OrderStatus.Filled)
        profit = 12 * 2.5 + 2 * 50
        self.assertEqual(self.Portfolio.getTotalValue(), 270 + profit)
        self.assertEqual(self.Portfolio.Cash, 270 + profit)

    def test_liquidate_security(self):
        self.Portfolio.Liquidate(FOO)
        self.broker.executeOrders()
        self.qc.SetOrderStatus(OrderStatus.Filled)
        profit = 12 * 2.5
        self.assertEqual(self.Portfolio.getTotalValue(), 270 + 100 + profit)
        self.assertEqual(self.Portfolio.Cash, 270 + profit)

    def test_buy_new_position(self):
        self.Portfolio.fillOrder('abc', 10, 20)
        self.assertEqual(len(self.Portfolio), 3)
        self.assertEqual(self.Portfolio['abc'].Quantity, 10)
        self.assertEqual(self.Portfolio.Cash, 70)

    def test_buy_existing_position_with_different_price(self):
        self.Portfolio.fillOrder(BAR, 1, 200)
        self.assertEqual(len(self.Portfolio), 2)
        self.assertEqual(self.Portfolio.Cash, 70)
        self.assertEqual(self.Portfolio[BAR].Quantity, 3)
        self.assertEqual(self.Portfolio[BAR].AveragePrice, 100)

    def test_sell_existing_position(self):
        self.Portfolio.fillOrder(FOO, -5, 4)
        self.assertEqual(len(self.Portfolio), 2)
        self.assertEqual(self.Portfolio.Cash, 290)
        self.assertEqual(self.Portfolio[FOO].Quantity, 7)

    def test_sell_existing_position_with_different_price(self):
        self.Portfolio.fillOrder(BAR, -1, 100)
        self.assertEqual(len(self.Portfolio), 2)
        self.assertEqual(self.Portfolio.Cash, 370)
        self.assertEqual(self.Portfolio[BAR].Quantity, 1)
        self.assertEqual(self.Portfolio[BAR].AveragePrice, 50)

    def test_sell_entire_position(self):
        self.Portfolio.fillOrder(FOO, -12, 4)
        self.assertEqual(len(self.Portfolio), 1)
        self.assertEqual(self.Portfolio.Cash, 318)

    def test_get_allocation_for_existing_position(self):
        self.assertEqual(self.Portfolio.getCurrentAllocation(BAR), 0.25)

    def test_get_allocation_for_non_existing_position(self):
        self.assertEqual(self.Portfolio.getCurrentAllocation(XYZ), 0.0)


class TestComplexTargetAllocations(unittest.TestCase):
    def setUp(self):
        self.price = {}
        self.price[FOO] = 10
        self.price[BAR] = 8
        self.price[XYZ] = 30

        self.qc = QCAlgorithm()
        self.qc.Securities = Securities([
            (FOO, self.price[FOO]),
            (BAR, self.price[BAR]),
            (XYZ, self.price[XYZ])
        ])
        self.broker = Broker(self.qc)
        self.qc.registerBroker(self.broker)
        self.Portfolio = Portfolio(parent=self.qc, broker=self.broker, cash=100)
        self.Portfolio.Cash = 40

    def test_target_allocation_in_portfolio_for_new_position_that_should_cause_a_sell(self):
        self.Portfolio[FOO] = Position(FOO, 2, self.price[FOO])  # 20
        self.Portfolio[BAR] = Position(BAR, 5, self.price[BAR])  # 40

        self.assertEqual(self.Portfolio.getCurrentAllocation(FOO), 0.2)
        self.assertAlmostEqual(self.Portfolio.getCurrentAllocation(BAR), 0.4)

        orders = self.Portfolio.getOrdersForTargetAllocation(FOO, 0.8)
        self.assertEqual(len(orders), 2)

        self.assertEqual(order_qty(orders, FOO), 6)
        self.assertAlmostEqual(order_qty(orders, BAR), -2.50, places=2)

    def test_target_allocation_in_portfolio_for_new_position_that_should_cause_three_orders(self):
        self.Portfolio[FOO] = Position(FOO, 2, self.price[FOO])  # 20
        self.Portfolio[BAR] = Position(BAR, 5, self.price[BAR])  # 40

        self.assertEqual(self.Portfolio.getCurrentAllocation(FOO), 0.2)
        self.assertAlmostEqual(self.Portfolio.getCurrentAllocation(BAR), 0.4)

        orders = self.Portfolio.getOrdersForTargetAllocation(XYZ, 0.5)
        self.assertEqual(len(orders), 3)

        self.assertAlmostEqual(order_qty(orders, FOO), -0.33, places=2)
        self.assertAlmostEqual(order_qty(orders, BAR), -0.83, places=2)
        self.assertAlmostEqual(order_qty(orders, XYZ), 1.67, places=2)

    def test_target_allocation_triggers_complete_sell(self):
        self.Portfolio[FOO] = Position(FOO, 2, self.price[FOO])  # 20
        self.Portfolio[BAR] = Position(BAR, 5, self.price[BAR])  # 40

        self.assertEqual(self.Portfolio.getCurrentAllocation(FOO), 0.2)
        self.assertAlmostEqual(self.Portfolio.getCurrentAllocation(BAR), 0.4)

        orders = self.Portfolio.getOrdersForTargetAllocation(XYZ, 1.0)
        self.assertEqual(len(orders), 3)

        self.assertEqual(order_qty(orders, FOO), -2)
        self.assertEqual(order_qty(orders, BAR), -5)
        self.assertAlmostEqual(order_qty(orders, XYZ), 3.33, places=2)


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
        self.qc.registerAlgorithms([self.portfolio])

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
        self.broker.addOrder(order)
        self.broker.executeOrders()
        self.assert_portfolio(self.broker.Portfolio, 0, {FOO: 98, BAR: 10, XYZ: 0})
        self.assert_portfolio(self.portfolio, 198, {FOO: 2, BAR: 0, XYZ: 0})
        self.assert_orders(self.qc.Transactions, {})

    def test_buying_ineexisting_stock_in_available_portfolio(self):
        order = Order(self.portfolio, XYZ, 1, order_type=OrderType.Market)

        # Adding and executing order.
        self.broker.addOrder(order)
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

import unittest


from mocked import QCAlgorithm, Securities, Security, Symbol
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
        self.Portfolio = Portfolio(parent=self.qc, cash=100)

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


class TestPortfolioWithSinglePosition(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm()
        self.qc.Securities = Securities([(FOO, 2.5), (BAR, 10)])
        self.Portfolio = Portfolio(parent=self.qc, cash=270)
        self.Portfolio[FOO] = Position(FOO, 12, 2.5)

    def test_total_value(self):
        self.assertEqual(self.Portfolio.getTotalValue(), 300)
        self.qc.Securities[FOO] = Security(FOO, price=3)
        self.assertEqual(self.Portfolio.getTotalValue(), 306)

    def test_buy_existing_position(self):
        self.Portfolio.fillOrder(FOO, 1, 9)
        self.assertEqual(self.Portfolio[FOO].Quantity, 13)
        self.assertEqual(self.Portfolio[FOO].cost, 3)
        self.assertEqual(self.Portfolio.Cash, 261)

    def test_sell_existing_position(self):
        self.Portfolio.fillOrder(FOO, -1, 3)
        self.assertEqual(self.Portfolio[FOO].Quantity, 11)
        self.assertEqual(self.Portfolio[FOO].cost, 2.5)
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
        self.qc = QCAlgorithm()
        self.qc.Securities = Securities([(FOO, 2.5), (BAR, 50)])
        self.Portfolio = Portfolio(parent=self.qc, cash=270)
        self.Portfolio[FOO] = Position(FOO, 12, 2.5) # 30
        self.Portfolio[BAR] = Position(BAR, 2, 50) # 100

    def test_total_value(self):
        self.assertEqual(self.Portfolio.getTotalValue(), 400)

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
        self.assertEqual(self.Portfolio[BAR].cost, 100)

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
        self.assertEqual(self.Portfolio[BAR].cost, 50)

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
        self.Portfolio = Portfolio(parent=self.qc, cash=100)
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


class TestMarketOrders(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm()
        self.qc.Securities = Securities([(FOO, 2.5)])
        self.broker = Broker(self.qc, 500)
        self.broker.Portfolio[FOO] = Position(FOO, 5, 10)

    def test_buy_from_avail_portfolio_first(self):
        portfolio = Portfolio(parent=self.qc, cash=100)
        order = Order(portfolio, FOO, 2, order_type=OrderType.Market)
        self.broker.addOrder(order)

        # Execure orders.
        self.assertEqual(len(self.broker.orders), 1)
        self.broker.executeOrders()
        self.assertEqual(len(self.broker.orders), 0)

        # Number of positions in market remains the same (1),
        # but in portfolio increased (0 to 1)
        self.assertEqual(len(self.broker.Portfolio), 1)
        self.assertEqual(len(portfolio), 1)

        # Remaining Quantity of position changed.
        remaining = self.broker.Portfolio[FOO].Quantity
        used = portfolio[FOO].Quantity
        self.assertEqual(remaining, 3)
        self.assertEqual(used, 2)

    def test_buy_from_broker_last(self):
        portfolio = Portfolio(parent=self.qc, cash=100)
        order = Order(portfolio, BAR, 2, order_type=OrderType.Market)
        self.broker.addOrder(order)

        # Execure orders.
        self.assertEqual(len(self.broker.orders), 1)
        self.broker.executeOrders()
        self.assertEqual(len(self.broker.orders), 0)

        # Number of positions in market remains the same (1),
        # but in portfolio increased (0 to 1)
        self.assertEqual(len(self.broker.Portfolio), 1)
        self.assertEqual(len(portfolio), 1) # order was executed

        # Remaining Quantity of position changed.
        self.assertEqual(self.broker.Portfolio[FOO].Quantity, 5)
        self.assertTrue(BAR not in self.broker.Portfolio)
        self.assertEqual(portfolio[BAR].Quantity, 2)

if __name__ == '__main__':
    unittest.main()

"""
MD5: 660b88c60092252853cd7fa26775e0b3
"""

from algorithm_manager import AlgorithmManager
from market import Singleton, Broker, BenchmarkSymbol
# from dual_momentum_algorithm import DualMomentumAlgorithm as DM
# from accelerated_dual_momentum_algorithm import AcceleratedDualMomentumAlgorithm as ADM
from macd_algorithm import MacdAlgorithm
from momentum_algorithm import MomentumAlgorithm
from dual_momentum_crypto_algorithm import DualMomentumAlgorithm

class MyAlgos(AlgorithmManager):
    def Initialize(self):
        Singleton.Setup(self, log_level=Singleton.LOG)
        # self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Cash)
        self.SetBrokerageModel(BrokerageName.GDAX, AccountType.Cash)
        # self.Portfolio.MarginCallModel = MarginCallModel.Null
        # Singleton.SetStartDateLogLevel(Singleton.DEBUG, 2018, 5, 15)

        cash_per_algo = 10000
        total_cash = 3 * cash_per_algo
        broker = Broker(total_cash)
        # algorithms = [
        #     DM(broker=broker, cash=cash_per_algo, options={"max_positions": 1, "cash": 'BND', "stocks": ['SPY', 'VTV'], 'signal': 'SPY', 'window': 100}, name="DM"),
        #     ADM(broker=broker, cash=cash_per_algo, options={"bonds": ["VUSTX"], "stocks": ["SPY", "VINEX"]}, name="ADM"),
        # ]
        # benchmarks = [ BenchmarkSymbol(ticker="SPY", name="SPY") ]

        algorithms = [
            DualMomentumAlgorithm(broker=broker, cash=cash_per_algo, options={"max_positions": 1, "stocks": ['BTCUSD', 'LTCUSD', 'ETHUSD'], 'signal': 'BTCUSD', 'window': 100}, name="DM"),
            MomentumAlgorithm(broker=broker, cash=cash_per_algo, name="Momentum"),
            MacdAlgorithm(broker=broker, cash=cash_per_algo, options={"moving_average_type": MovingAverageType.Exponential}, name="MACD"),
        ]
        benchmarks = [ BenchmarkSymbol(ticker="BTCUSD", name="BTC", crypto=True) ]

        # Backtest only.
        # self.SetStartDate(2009, 1, 8) # min
        self.SetStartDate(2015, 9, 1)
        # self.SetEndDate(2020, 12, 28)
        self.SetCash(cash_per_algo * len(algorithms))
        # self.SetBenchmark("SPY")

        self.registerAlgorithms(algorithms, benchmarks)
from market import Singleton, AlgorithmManager, BenchmarkSymbol
# from dual_momentum_algorithm import DualMomentumAlgorithm as DM
# from accelerated_dual_momentum_algorithm import AcceleratedDualMomentumAlgorithm as ADM
from macd_algorithm import MACDTrendAlgorithm
from momentum_algorithm import MomentumAlgorithm
from dual_momentum_crypto_algorithm import DualMomentumAlgorithm

class MyAlgos(AlgorithmManager):
    def Initialize(self):
        Singleton.Setup(self, log_level=Singleton.LOG)

        cash_per_algo = 10_000
        algorithms = [
            # DualMomentumAlgorithm(cash=cash_per_algo, options={"max_positions": 1, "stocks": ['BTCUSD', 'LTCUSD', 'ETHUSD'], 'signal': 'BTCUSD', 'window': 100}, name="DM"),
            # MomentumAlgorithm(cash=cash_per_algo, name="Momentum"),
            MACDTrendAlgorithm(cash=cash_per_algo, options={"moving_average_type": MovingAverageType.Exponential}, name="MACD"),
        ]
        benchmarks = [
            BenchmarkSymbol(ticker="BTCUSD", name="BTC", security_type=SecurityType.Crypto),
            BenchmarkSymbol(ticker="LTCUSD", name="LTC", security_type=SecurityType.Crypto),
            BenchmarkSymbol(ticker="ETHUSD", name="ETH", security_type=SecurityType.Crypto)
        ]
        total_cash = cash_per_algo * len(algorithms)

        # self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Cash)
        self.SetBrokerageModel(BrokerageName.GDAX, AccountType.Cash)
        # self.Portfolio.MarginCallModel = MarginCallModel.Null

        # Singleton.SetStartDateLogLevel(Singleton.DEBUG, 2018, 5, 15)
        # self.SetStartDate(2009, 1, 8) # min
        self.SetStartDate(2015, 9, 1)
        self.SetEndDate(2016, 12, 28)
        self.SetCash(total_cash)
        # self.SetBenchmark("SPY")

        self.registerAlgorithms(algorithms, benchmarks)

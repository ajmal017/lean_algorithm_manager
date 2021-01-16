class CoinbaseFeeModel(FeeModel):
    def __init__(self, algorithm):
        self.algorithm = algorithm

    def GetOrderFee(self, parameters):
        order = parameters.Order
        security = parameters.Security

        unitPrice = security.AskPrice if order.Direction == OrderDirection.Buy else security.BidPrice
        unitPrice = unitPrice * security.SymbolProperties.ContractMultiplier

        # currently we do not model 30-day volume, so we use the first tier
        isMaker = order.Type == OrderType.Limit and not order.IsMarketable
        feePercentage = 0.0050  # 0.50%
        fee = unitPrice * order.AbsoluteQuantity * feePercentage

        return OrderFee(CashAmount(fee, security.QuoteCurrency.Symbol))


# Setup Python

1. Install Pyenv: https://github.com/pyenv/pyenv

2. Install python 2.7.14
```
pyenv install -v 2.7.14
```
Or on MacOS with homebrew:
```
PYTHON_CONFIGURE_OPTS="--enable-framework" CFLAGS="-I$(brew --prefix openssl)/include" LDFLAGS="-L$(brew --prefix openssl)/lib" pyenv install -v 2.7.14
```

3. Install requirements
```
pip install unittest2
```


# Tests

```
python -m unittest discover -s test
```


# Notes

Algorithm: Independent algorithm that contains a Portfolio with Positions. We can only have one Portfolio per algorithm, but we can have multiple algorithms.

Portfolio: Set of positions and cash. Globally, we can have several algorithms, each one with its own Portfolio. The sum of all the portfolios cannot exceed the underlying global Broker's Portfolio.

Position: current position (long/short) in a given Portfolio. Globally, we can have several Positions with the same symbol, but only one in a single Portfolio.

Broker: Middleware between Portfolio actions (buy/sell) and Broker/Lean. This layer manages the overall positions across all algorithms. On startup, it loads the existing real brokers positions, which are made available before actually buying real positions. Might minimize buy/sell if they happen to match across algorithms.


# TODO

BUGS
? Fix trade tags not showing

QUICK
- Main.SetWarmup() is Max of algos SetWarmup()
- Trades made in available portfolio should trigger alg.OnOrderHandle
- self.Liquidate(Symbol = None) -> calls Portfolio.Liquidate(Symbol = None)
- main.SetCash() sets Broker.portfolio.Cash and raises Exception if sum(algs.Cash)

COMPLEX
- Consolidate orders at Broker level to minimize unnecessary trades
- Automatic portfolios' performance plotting

ICEBOX:
? self.Transactions(?)
- Add defensive guards all over the code
- Startup loading of IB portfolio, eg, sets Broker.portfolio.Cash and raises Exception if sum(algs.Cash)
- Support Virtual Portofio/Alg to protect existing positions


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

3. Install requirments
```
pip install unittest2
```

# NOTES

Algorithm: (aka Portfolio) independent algorithm (consisting of Positions) pertaining a single algorithm

Position: current position (long/short) in a given Algorithm. We can have multiple Positions with the same symbol

Broker: Middleware between Portfolio actions (buy/sell) and Broker/Lean. This layer manages the overall positions across all algorithms. On startup, it loads the existing real brokers positions, which are made available before actually buying real positions. Might minimize buy/sell if they happen to match across algorithms.

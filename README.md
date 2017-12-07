
# Setup Python

1. Install Pyenv: https://github.com/pyenv/pyenv

2. Install python 2.7.14
```
PYTHON_CONFIGURE_OPTS="--enable-framework" CFLAGS="-I$(brew --prefix openssl)/include" LDFLAGS="-L$(brew --prefix openssl)/lib" pyenv install -v 2.7.14
```

3. Install requirments
```
pip install -r requirements.txt
```



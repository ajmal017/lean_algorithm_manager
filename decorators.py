from functools import wraps
import functools

def accepts(**types):
    def check_accepts(f):
        assert len(types) == f.__code__.co_argcount, \
            'wrong number of arguments in "%s"' % f.__name__

        def wrapper(*args, **kwargs):
            for i, v in enumerate(args):
                if f.__code__.co_varnames[i] in types and \
                        not isinstance(v, types[f.__code__.co_varnames[i]]):
                    raise Exception("arg '%s'=%r does not match %s" %
                                    (f.__code__.co_varnames[i], v, types[f.__code__.co_varnames[i]]))
                    # del types[f.__code__.co_varnames[i]]

            for k, v in iter(kwargs.items()):
                if k in types and not isinstance(v, types[k]):
                    raise Exception("arg '%s'=%r does not match %s" %
                                    (k, v, types[k]))

            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return check_accepts


def convert_to_symbol(arg_name, make_symbol_func):
    def make_wrapper(f):
        if hasattr(f, "wrapped_args"):
            wrapped_args = getattr(f, "wrapped_args")
        else:
            code = f.__code__
            wrapped_args = list(code.co_varnames[:code.co_argcount])

        try:
            arg_index = wrapped_args.index(arg_name)
        except ValueError:
            raise NameError(arg_name)

        def wrapper(*args, **kwargs):
            if arg_index < len(args):
                ticker = args[arg_index]
                if isinstance(ticker, str):
                    args = list(args)
                    args[arg_index] = make_symbol_func(ticker)
            else:
                if arg_name in kwargs:
                    ticker = kwargs[arg_name]
                    if isinstance(ticker, str):
                        kwargs[arg_name] = make_symbol_func(ticker)

            return f(*args, **kwargs)

        wrapper.wrapped_args = wrapped_args
        return wrapper

    return make_wrapper

####################################################################################

def all_methods(decorator):
    @wraps(decorator)
    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)):
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate

def post(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        retval = func(*args, **kwargs)
        if len(args) > 0:
            attr = getattr(args[0], f"_AlgorithmManager__post", None)
            if callable(attr):
                attr()
        return retval
    return wrapper

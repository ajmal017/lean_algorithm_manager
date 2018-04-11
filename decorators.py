"""
MD5: d6dec1c2f9007af5426dc16dc3b7dbbb
"""


class _DelegatedAttribute(object):
    def __init__(self, delegator_name, attr_name, baseclass):
        self.attr_name = attr_name
        self.delegator_name = delegator_name
        self.baseclass = baseclass

    def __get__(self, instance, klass):
        if instance is None:
            # klass.DelegatedAttr() -> baseclass.attr
            return getattr(self.baseclass, self.attr_name)
        else:
            # instance.DelegatedAttr() -> instance.delegate.attr
            return getattr(self.delegator(instance), self.attr_name)

    def __set__(self, instance, value):
        # instance.delegate.attr = value
        setattr(self.delegator(instance), self.attr_name, value)

    def __delete__(self, instance):
        delattr(self.delegator(instance), self.attr_name)

    def delegator(self, instance):
        # minor syntactic sugar to help remove "getattr" spam (marginal utility)
        return getattr(instance, self.delegator_name)

    def __str__(self):
        return ""


def delegates_to_old(baseclass, delegator='delegate', include=None, exclude=None):
    '''A decorator to customize inheritance of the decorated class from the
    given baseclass. `delegator` is the name of the attribute on the subclass
    through which delegation is done;  `include` and `exclude` are a whitelist
    and blacklist of attrs to include from baseclass.__dict__, providing the
    main customization hooks.'''
    # `autoincl` is a boolean describing whether or not to include all of baseclass.__dict__

    # turn include and exclude into sets, if they aren't already
    if not isinstance(include, set):
        include = set(include) if include else set()
    if not isinstance(exclude, set):
        exclude = set(exclude) if exclude else set()

    # delegated_attrs = set(baseclass.__dict__.keys()) if autoincl else set()
    # Couldn't get the above line to work, because delegating __new__ fails miserably
    delegated_attrs = set()
    attributes = (include | delegated_attrs) - exclude

    def wrapper(subclass):
        ## create property for storing the delegate
        #setattr(subclass, delegator, None)
        # ^ Initializing the delegator is the duty of the subclass itself, this
        # decorator is only a tool to create attrs that go through it

        # don't bother adding attributes that the class already has
        attrs = attributes - set(subclass.__dict__.keys())

        # set all the attributes
        for attr in attrs:
            setattr(subclass, attr, _DelegatedAttribute(delegator, attr, baseclass))

        # for attr in exclude:
        #     if hasattr(subclass, attr):
        #         delattr(subclass, attr)

        return subclass

    return wrapper


def delegates_to(cls):
    class Wrapper(object):
        def __init__(self, *args, **kwargs):
            self.wrapped = cls(*args, **kwargs)
            # self.parent = kwargs['parent'] if 'parent' in kwargs else args[0]
            # setattr(self.wrapped, '_parent', self.parent)

        def __getattr__(self, attr):
            """Delegate to parent."""
            if hasattr(self.wrapped, attr):
                return getattr(self.wrapped, attr)
            elif hasattr(self.wrapped._parent, attr):
                print("Delegating to parent: {}".format(attr))
                return getattr(self.wrapped._parent, attr)
            else:
                raise AttributeError(attr)

    return Wrapper

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
                    # print("Converted string \"{}\" to Symbol \"{}\"".format(ticker, args[arg_index]))
            else:
                if arg_name in kwargs:
                    ticker = kwargs[arg_name]
                    if isinstance(ticker, str):
                        kwargs[arg_name] = make_symbol_func(ticker)
                        # print("Converted string \"{}\" to Symbol \"{}\"".format(ticker, args[arg_index]))

            return f(*args, **kwargs)

        wrapper.wrapped_args = wrapped_args
        return wrapper

    return make_wrapper

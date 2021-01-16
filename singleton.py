from datetime import timedelta, date
import bisect

class SingletonMeta(type):
    def __getattr__(cls, attr):
        """Delegate to parent."""
        if hasattr(cls.QCAlgorithm, attr):
            return getattr(cls.QCAlgorithm, attr)
        else:
            raise AttributeError(attr)


class Singleton(metaclass=SingletonMeta):
    ERROR = 0
    LOG = 1
    DEBUG = 2

    Today = date(1, 1, 1)
    QCAlgorithm = None
    LogLevel = LOG
    _log_level_dates = []
    _warm_up = None
    _warm_up_from_algorithm = False

    @classmethod
    def Setup(cls, parent, broker=None, email_addr=None, log_level=LOG):
        cls.Today = date(1, 1, 1)
        cls.QCAlgorithm = parent
        cls.Broker = broker
        cls.LogLevel = log_level
        cls._warm_up = None
        cls._warm_up_from_algorithm = False
        cls._lot_size_decimal_places = None
        cls.Email = Email(email_addr) if email_addr else None

    @classmethod
    def _update_time(cls):
        if cls.Today != cls.QCAlgorithm.Time.date():
            cls.Today = cls.QCAlgorithm.Time.date()
            cls.Debug(" - - - - {} - - - - ".format(cls.Today))

    @classmethod
    def SetStartDateLogLevel(cls, log_level, year, month, day):
        bisect.insort(cls._log_level_dates,
                      (date(year, month, day), log_level))

    @classmethod
    def _can_log(cls, log_level):
        matched_log_level = cls.LogLevel
        for elem in cls._log_level_dates:
            if elem[0] <= cls.Today:
                matched_log_level = elem[1]
            else:
                break
        return log_level <= matched_log_level

    @classmethod
    def Log(cls, message):
        if cls._can_log(cls.LOG):
            cls._update_time()
            cls.QCAlgorithm.Log("L " + message)

    @classmethod
    def Debug(cls, message):
        if cls._can_log(cls.DEBUG):
            cls._update_time()
            cls.QCAlgorithm.Log("D " + message)

    @classmethod
    def Error(cls, message):
        if cls._can_log(cls.ERROR):
            cls._update_time()
            cls.QCAlgorithm.Error("E " + message)

    @classmethod
    def CreateSymbol(cls, ticker):
        return cls.QCAlgorithm.Securities[ticker].Symbol

    @classmethod
    def _convert_period_to_int(cls, period):
        if isinstance(period, timedelta):
            return period.days
        return period

    @classmethod
    def _set_warm_up(cls, period):
        period = cls._convert_period_to_int(period)
        cls._warm_up = period
        cls.QCAlgorithm.SetWarmUp(period)

    @classmethod
    def SetWarmUp(cls, period):
        if not cls._warm_up_from_algorithm:
            cls._set_warm_up(period)

    @classmethod
    def SetWarmUpFromAlgorithm(cls, period):
        period = cls._convert_period_to_int(period)
        cls._warm_up_from_algorithm = True
        if not cls._warm_up or period > cls._warm_up:
            cls._set_warm_up(period)


class Email(object):
    def __init__(self):
        self.__address = None
        self.Content = ""

    def SetEmailAddress(self, email_addr):
        self.__address = email_addr

    def AppendText(self, text):
        if not self.__address:
            return
        self.Content += f"<tr><td colspan=\"2\">{text}</td></tr>\n"

    def AppendKeyValue(self, key, value):
        if not self.__address:
            return
        self.Content += f"<tr><td>{key}</td><td>{value}</td></tr>\n"

    @property
    def HasContent(self):
        return bool(self.Content)

    def Send(self, subject):
        Singleton.Debug(f"> Sending email \"{subject}\"")
        if not self.__address:
            return
        body = "<html><body><table>" + self.Content + "</table></body></html>"
        self.Content = ""
        Singleton.QCAlgorithm.Notify.Email(self.__address, subject, body)

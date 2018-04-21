# pylint: disable=C0111,C0103,C0112,W0201,W0212
import unittest

from datetime import date
from market import Singleton
from algorithm_manager import AlgorithmManager as QCAlgorithm


def assert_log_level_error(test):
    test.assertEqual(Singleton.LogLevelPrintable(Singleton.ERROR), True)
    test.assertEqual(Singleton.LogLevelPrintable(Singleton.INFO), False)
    test.assertEqual(Singleton.LogLevelPrintable(Singleton.LOG), False)
    test.assertEqual(Singleton.LogLevelPrintable(Singleton.DEBUG), False)

def assert_log_level_info(test):
    test.assertEqual(Singleton.LogLevelPrintable(Singleton.ERROR), True)
    test.assertEqual(Singleton.LogLevelPrintable(Singleton.INFO), True)
    test.assertEqual(Singleton.LogLevelPrintable(Singleton.LOG), False)
    test.assertEqual(Singleton.LogLevelPrintable(Singleton.DEBUG), False)

def assert_log_level_log(test):
    test.assertEqual(Singleton.LogLevelPrintable(Singleton.ERROR), True)
    test.assertEqual(Singleton.LogLevelPrintable(Singleton.INFO), True)
    test.assertEqual(Singleton.LogLevelPrintable(Singleton.LOG), True)
    test.assertEqual(Singleton.LogLevelPrintable(Singleton.DEBUG), False)

def assert_log_level_debug(test):
    test.assertEqual(Singleton.LogLevelPrintable(Singleton.ERROR), True)
    test.assertEqual(Singleton.LogLevelPrintable(Singleton.INFO), True)
    test.assertEqual(Singleton.LogLevelPrintable(Singleton.LOG), True)
    test.assertEqual(Singleton.LogLevelPrintable(Singleton.DEBUG), True)


class TestSingletonLogLevel(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm()
        Singleton.Setup(self.qc, log_level=Singleton.INFO)

    def test_log_level_printable_error(self):
        Singleton.LogLevel = Singleton.ERROR
        assert_log_level_error(self)

    def test_log_level_printable_info(self):
        Singleton.LogLevel = Singleton.INFO
        assert_log_level_info(self)

    def test_log_level_printable_log(self):
        Singleton.LogLevel = Singleton.LOG
        assert_log_level_log(self)

    def test_log_level_printable_debug(self):
        Singleton.LogLevel = Singleton.DEBUG
        assert_log_level_debug(self)


class TestSingletonLogLevelWithCustomDateRanges(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm()
        Singleton.Setup(self.qc, log_level=Singleton.INFO)

    @classmethod
    def setUpClass(cls):
        Singleton.SetStartDateLogLevel(Singleton.LOG, 2005, 5, 1)
        Singleton.SetStartDateLogLevel(Singleton.INFO, 2006, 10, 31)
        Singleton.SetStartDateLogLevel(Singleton.ERROR, 2006, 11, 3)
        Singleton.SetStartDateLogLevel(Singleton.LOG, 2007, 5, 1)
        Singleton.SetStartDateLogLevel(Singleton.DEBUG, 2008, 10, 31)

    def test_dates_setup(self):
        assert_log_level_info(self)

    def test_dates_simple(self):
        Singleton.Time = date(2004, 10, 25)
        assert_log_level_info(self)

        Singleton.Time = date(2005, 10, 25)
        assert_log_level_log(self)

        Singleton.Time = date(2005, 11, 25)
        assert_log_level_log(self)

        Singleton.Time = date(2006, 11, 1)
        assert_log_level_info(self)

        Singleton.Time = date(2006, 11, 4)
        assert_log_level_error(self)

        Singleton.Time = date(2007, 11, 1)
        assert_log_level_log(self)

        Singleton.Time = date(2018, 11, 1)
        assert_log_level_debug(self)

    def test_dates_limit(self):
        Singleton.Time = date(2007, 4, 30)
        assert_log_level_error(self)
        Singleton.Time = date(2007, 5, 1)
        assert_log_level_log(self)

        Singleton.Time = date(2006, 11, 2)
        assert_log_level_info(self)
        Singleton.Time = date(2006, 11, 3)
        assert_log_level_error(self)


if __name__ == '__main__':
    unittest.main()

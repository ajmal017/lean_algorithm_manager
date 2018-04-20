# pylint: disable=C0111,C0103,C0112,W0201,W0212
import unittest

from market import Singleton
from algorithm_manager import AlgorithmManager as QCAlgorithm

class TestSingleton(unittest.TestCase):
    def setUp(self):
        self.qc = QCAlgorithm()
        Singleton.Setup(self.qc, log_level=Singleton.INFO)

    def test_log_level_printable_error(self):
        Singleton.LogLevel = Singleton.ERROR
        self.assertEqual(Singleton.LogLevelPrintable(Singleton.ERROR), True)
        self.assertEqual(Singleton.LogLevelPrintable(Singleton.INFO), False)
        self.assertEqual(Singleton.LogLevelPrintable(Singleton.LOG), False)
        self.assertEqual(Singleton.LogLevelPrintable(Singleton.DEBUG), False)

    def test_log_level_printable_info(self):
        Singleton.LogLevel = Singleton.INFO
        self.assertEqual(Singleton.LogLevelPrintable(Singleton.ERROR), True)
        self.assertEqual(Singleton.LogLevelPrintable(Singleton.INFO), True)
        self.assertEqual(Singleton.LogLevelPrintable(Singleton.LOG), False)
        self.assertEqual(Singleton.LogLevelPrintable(Singleton.DEBUG), False)

    def test_log_level_printable_log(self):
        Singleton.LogLevel = Singleton.LOG
        self.assertEqual(Singleton.LogLevelPrintable(Singleton.ERROR), True)
        self.assertEqual(Singleton.LogLevelPrintable(Singleton.INFO), True)
        self.assertEqual(Singleton.LogLevelPrintable(Singleton.LOG), True)
        self.assertEqual(Singleton.LogLevelPrintable(Singleton.DEBUG), False)

    def test_log_level_printable_debug(self):
        Singleton.LogLevel = Singleton.DEBUG
        self.assertEqual(Singleton.LogLevelPrintable(Singleton.ERROR), True)
        self.assertEqual(Singleton.LogLevelPrintable(Singleton.INFO), True)
        self.assertEqual(Singleton.LogLevelPrintable(Singleton.LOG), True)
        self.assertEqual(Singleton.LogLevelPrintable(Singleton.DEBUG), True)


if __name__ == '__main__':
    unittest.main()

import logging
import unittest

log = logging.getLogger(__name__)


class Testing(unittest.TestCase):
    def testing(self):
        self.assertEqual('foo', 'foo')

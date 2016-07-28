import unittest
from .. import pluck


class PluckTest(unittest.TestCase):
    def find_indices_test(self):
        self.assertEqual([0, 2], list(pluck.find_indices('aba', 'a')))
        self.assertEqual([], list(pluck.find_indices('aba', 'c')))
        self.assertEqual([1], list(pluck.find_indices('aba', 'ba')))

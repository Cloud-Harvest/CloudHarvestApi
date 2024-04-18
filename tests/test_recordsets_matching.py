import unittest
from collections import OrderedDict
from data import matching


class TestMatching(unittest.TestCase):
    """
    Test case for the classes in matching.py
    """

    def test_HarvestMatch(self):
        """
        Test the HarvestMatch class with different types of inputs
        """
        # Test creating a HarvestMatch object and calling the match method
        record = OrderedDict([('key1', 'value1'), ('key2', 'value2')])
        syntax = 'key1=value1'
        match = matching.HarvestMatch(record=record, syntax=syntax)
        self.assertTrue(match.match())
        self.assertEqual(match.final_match_operation, 'value1=value1')
        self.assertTrue(match.is_match)

        # Test creating a HarvestMatch object with a non-matching record
        record = OrderedDict([('key1', 'value1'), ('key2', 'value2')])
        syntax = 'key1=value2'
        match = matching.HarvestMatch(record=record, syntax=syntax)
        self.assertFalse(match.match())
        self.assertEqual(match.final_match_operation, 'value1=value2')
        self.assertFalse(match.is_match)

    def test_HarvestMatchSet(self):
        """
        Test the HarvestMatchSet class with different types of inputs
        """
        # Test creating a HarvestMatchSet object
        record = OrderedDict([('key1', 'value1'), ('key2', 'value2')])
        syntax = 'key1=value1'
        matches = ['key1=value1', 'key2=value2']
        match_set = matching.HarvestMatchSet(record, syntax, matches)
        self.assertEqual(len(match_set.matches), 2)

        # Test creating a HarvestMatchSet object with no matches
        record = OrderedDict([('key1', 'value1'), ('key2', 'value2')])
        syntax = 'key1=value1'
        matches = []
        match_set = matching.HarvestMatchSet(record, syntax, matches)
        self.assertEqual(len(match_set.matches), 0)


if __name__ == '__main__':
    unittest.main()

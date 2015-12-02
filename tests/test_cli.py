from unittest import TestCase
from oscqam import formatters
from oscqam.actions import multi_level_sort


class ListOutputTests(TestCase):
    def test_multi_level_sort(self):
        one = {'a': 0, 'b': 1}
        two = {'a': 0, 'b': 0}
        xs = [one, two]
        criteria = [lambda x: x['b'],
                    lambda x: x['a']]
        sortedxs = multi_level_sort(xs, criteria)
        self.assertEqual(sortedxs[0], two)
        self.assertEqual(sortedxs[1], one)

    def test_lineseperators(self):
        line = formatters.os_lineseps('Test\n', target = 'Windows')
        self.assertEqual(line, 'Test\r\n')
        line = formatters.os_lineseps('Test\r\n', target = 'Windows')
        self.assertEqual(line, 'Test\r\n')

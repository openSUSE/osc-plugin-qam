import os
from unittest import TestCase
from oscqam import cli


class ListOutputTests(TestCase):
    def test_tabular_output_split_lists(self):
        """Tabular output should split lists into newlines.
        """
        data = [[["a", "b"], "c"]]
        output = cli.tabular_output(data, ["A", "B"])
        expected = os.linesep.join(["+---+---+",
                                    "| A | B |",
                                    "+---+---+",
                                    "| a | c |",
                                    "| b |   |",
                                    "+---+---+"])
        self.assertEqual(expected, output.get_string())

    def test_verbose_output_joins_lists(self):
        """Verbose output should join lists into a single line.
        """
        data = [[["a", "b"], "c"]]
        output = cli.verbose_output(data, ["A", "B"])
        expected = os.linesep.join(["A: a, b",
                                    "B: c",
                                    "-----------------------"])
        self.assertEqual(expected, output)

    def test_multi_level_sort(self):
        one = {'a': 0, 'b': 1}
        two = {'a': 0, 'b': 0}
        xs = [one, two]
        criteria = [lambda x: x['b'],
                    lambda x: x['a']]
        sortedxs = cli.multi_level_sort(xs, criteria)
        self.assertEqual(sortedxs[0], two)
        self.assertEqual(sortedxs[1], one)

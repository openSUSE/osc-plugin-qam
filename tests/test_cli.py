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

import __builtin__

from decorator import contextmanager
from unittest import TestCase
import sys

from oscqam import formatters, cli
from oscqam.actions import multi_level_sort


@contextmanager
def wrap_builtin(answer):
    raw_input = __builtin__.raw_input
    __builtin__.raw_input = lambda x: answer
    yield
    __builtin__.raw_input = raw_input


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

    def test_yes_no_question_true(self):
        interpreter = cli.QamInterpreter(None)
        with wrap_builtin('yes'):
            result = interpreter.yes_no("Sure about that")
            self.assertEqual(result, True)
        with wrap_builtin('Y'):
            result = interpreter.yes_no("Sure about that")
            self.assertEqual(result, True)
        with wrap_builtin('yEs'):
            result = interpreter.yes_no("Sure about that")
            self.assertEqual(result, True)

    def test_yes_no_question_false(self):
        interpreter = cli.QamInterpreter(None)
        with wrap_builtin('no'):
            result = interpreter.yes_no("Sure about that")
            self.assertEqual(result, False)
        with wrap_builtin('n'):
            result = interpreter.yes_no("Sure about that")
            self.assertEqual(result, False)
        with wrap_builtin('nO'):
            result = interpreter.yes_no("Sure about that")
            self.assertEqual(result, False)

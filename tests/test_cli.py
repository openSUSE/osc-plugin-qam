import builtins

from contextlib import contextmanager

from oscqam import formatters, cli
from oscqam.utils import multi_level_sort


@contextmanager
def wrap_builtin(answer):
    raw_input = builtins.input
    builtins.input = lambda x: answer
    yield
    builtins.input = raw_input


def test_multi_level_sort():
    one = {"a": 0, "b": 1}
    two = {"a": 0, "b": 0}
    xs = [one, two]
    criteria = [lambda x: x["b"], lambda x: x["a"]]
    sortedxs = multi_level_sort(xs, criteria)
    assert sortedxs[0] == two
    assert sortedxs[1] == one


def test_lineseperators():
    line = formatters.os_lineseps("Test\n", target="Windows")
    assert line == "Test\r\n"
    line = formatters.os_lineseps("Test\r\n", target="Windows")
    assert line == "Test\r\n"


def test_yes_no_question_true():
    interpreter = cli.QamInterpreter(None)
    with wrap_builtin("yes"):
        result = interpreter.yes_no("Sure about that")
        assert result
    with wrap_builtin("Y"):
        result = interpreter.yes_no("Sure about that")
        assert result
    with wrap_builtin("yEs"):
        result = interpreter.yes_no("Sure about that")
        assert result


def test_yes_no_question_false():
    interpreter = cli.QamInterpreter(None)
    with wrap_builtin("no"):
        result = interpreter.yes_no("Sure about that")
        assert result is False
    with wrap_builtin("n"):
        result = interpreter.yes_no("Sure about that")
        assert result is False
    with wrap_builtin("nO"):
        result = interpreter.yes_no("Sure about that")
        assert result is False

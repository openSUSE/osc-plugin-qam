import argparse
import builtins

from contextlib import contextmanager

from oscqam import cli_approve, cli_assign, cli_reject, formatters
from oscqam.errors import NotPreviousReviewerError
from oscqam.reject_reasons import RejectReason
from oscqam.utils import multi_level_sort
from oscqam.common import Common


@contextmanager
def wrap_builtin(answer):
    raw_input = builtins.input
    builtins.input = lambda x: answer
    yield
    builtins.input = raw_input


def make_args(**kwargs):
    """Build a command-line argument namespace with sensible defaults."""
    defaults = {
        "apiurl": "https://api.example.com",
        "user": "anonymous",
        "request_id": "12345",
        "skip_template": False,
        "group": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def make_command(command_class):
    """Instantiate a QAM osc command without argparse wiring."""
    return command_class.__new__(command_class)


def recording_action():
    """Return an action stand-in class and the list of created instances."""
    created = []

    class Recorder:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            self.calls = 0
            created.append(self)

        def __call__(self):
            self.calls += 1

    return Recorder, created


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
    interpreter = Common
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
    interpreter = Common
    with wrap_builtin("no"):
        result = interpreter.yes_no("Sure about that")
        assert result is False
    with wrap_builtin("n"):
        result = interpreter.yes_no("Sure about that")
        assert result is False
    with wrap_builtin("nO"):
        result = interpreter.yes_no("Sure about that")
        assert result is False


def test_template_skip_from_args():
    common = Common()
    assert common.template_skip_from_args(make_args(skip_template=True)) is True
    assert common.template_skip_from_args(make_args(skip_template=False)) is False
    assert common.template_skip_from_args(argparse.Namespace()) is False


def test_approve_user_passes_skip_template(monkeypatch, remote):
    recorder, created = recording_action()
    monkeypatch.setattr(cli_approve, "ApproveUserAction", recorder)
    monkeypatch.setattr("oscqam.common.RemoteFacade", lambda apiurl: remote)
    command = make_command(cli_approve.QAMApproveCommand)
    command.run(make_args(skip_template=True))
    assert len(created) == 1
    action = created[0]
    assert action.args == (remote, "anonymous", "12345", "anonymous", True)
    assert action.calls == 1


def test_approve_group_passes_skip_template(monkeypatch, remote):
    recorder, created = recording_action()
    monkeypatch.setattr(cli_approve, "ApproveGroupAction", recorder)
    monkeypatch.setattr("oscqam.common.RemoteFacade", lambda apiurl: remote)
    command = make_command(cli_approve.QAMApproveCommand)
    with wrap_builtin("n"):  # do not abort the group approval
        command.run(make_args(group="qam-test", skip_template=False))
    assert len(created) == 1
    action = created[0]
    assert action.args == (remote, "anonymous", "12345", "qam-test", False)
    assert action.calls == 1


def test_approve_group_abort(monkeypatch, remote):
    recorder, created = recording_action()
    monkeypatch.setattr(cli_approve, "ApproveGroupAction", recorder)
    monkeypatch.setattr("oscqam.common.RemoteFacade", lambda apiurl: remote)
    command = make_command(cli_approve.QAMApproveCommand)
    with wrap_builtin("y"):  # abort the group approval
        command.run(make_args(group="qam-test"))
    assert created == []


def test_assign_passes_template_required(monkeypatch, remote):
    recorder, created = recording_action()
    monkeypatch.setattr(cli_assign, "AssignAction", recorder)
    monkeypatch.setattr("oscqam.common.RemoteFacade", lambda apiurl: remote)
    command = make_command(cli_assign.QAMAssignCommand)
    command.run(make_args(skip_template=True))
    assert len(created) == 1
    action = created[0]
    assert action.args == (remote, "anonymous", "12345", None)
    assert action.kwargs == {"template_required": False}
    assert action.calls == 1


def test_assign_retries_for_previous_reviewer(monkeypatch, remote):
    recorder, created = recording_action()

    class RaiseFirst(recorder):
        def __call__(self):
            super().__call__()
            if self is created[0]:
                raise NotPreviousReviewerError(["some_reviewer"])

    monkeypatch.setattr(cli_assign, "AssignAction", RaiseFirst)
    monkeypatch.setattr("oscqam.common.RemoteFacade", lambda apiurl: remote)
    command = make_command(cli_assign.QAMAssignCommand)
    with wrap_builtin("y"):  # force assignment despite not being a previous reviewer
        command.run(make_args(skip_template=True, group=["qam-test"]))
    assert len(created) == 2
    action = created[1]
    assert action.args == (remote, "anonymous", "12345", ["qam-test"])
    assert action.kwargs == {"template_required": False, "force": True}
    assert action.calls == 1


def test_assign_no_force_returns(monkeypatch, remote):
    recorder, created = recording_action()

    class RaiseFirst(recorder):
        def __call__(self):
            super().__call__()
            raise NotPreviousReviewerError(["some_reviewer"])

    monkeypatch.setattr(cli_assign, "AssignAction", RaiseFirst)
    monkeypatch.setattr("oscqam.common.RemoteFacade", lambda apiurl: remote)
    command = make_command(cli_assign.QAMAssignCommand)
    with wrap_builtin("n"):  # do not force the assignment
        command.run(make_args())
    assert len(created) == 1


def test_reject_passes_template_skip(monkeypatch, remote):
    recorder, created = recording_action()
    monkeypatch.setattr(cli_reject, "RejectAction", recorder)
    monkeypatch.setattr("oscqam.common.RemoteFacade", lambda apiurl: remote)
    command = make_command(cli_reject.QAMRejectCommand)
    command.run(make_args(skip_template=True, message="broken", reason=["admin"]))
    assert len(created) == 1
    action = created[0]
    assert action.args == (
        remote,
        "anonymous",
        "12345",
        [RejectReason.administrative],
        False,
        "broken",
    )
    assert action.calls == 1

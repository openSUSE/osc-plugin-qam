import os
import unittest
from oscqam import actions, models
from .mockremote import MockRemote


path = os.path.join(os.path.dirname(__file__), 'data')


def read_path(path):
    return open(path).read()


class UndoAction(actions.OscAction):
    def __init__(self):
        # Don't call super to prevent query to model objects.
        self.undo_stack = []
        self.undos = []

    def action(self):
        self.undo_stack.append(lambda: self.undos.append(1))
        raise models.RemoteError(None, None, None, None, None)


class ActionTests(unittest.TestCase):

    def setUp(self):
        self.mock_remote = MockRemote()

    def test_undo(self):
        u = UndoAction()
        u()
        self.assertEqual(u.undos, [1])

    def test_infer_no_groups_match(self):
        assign_action = actions.AssignAction(self.mock_remote, 'anonymous',
                                             '12345')
        self.assertRaises(actions.UninferableError, assign_action)

    def test_infer_groups_match(self):
        assign_action = actions.AssignAction(self.mock_remote, 'anonymous',
                                             '34567')
        self.assertRaises(actions.UninferableError, assign_action)

    def test_unassign_explicit_group(self):
        unassign = actions.UnassignAction(self.mock_remote, 'anonymous',
                                          '23456', 'qam-sle')
        unassign()
        self.assertEqual(len(self.mock_remote.post_calls), 2)

    def test_unassign_inferred_group(self):
        unassign = actions.UnassignAction(self.mock_remote, 'anonymous',
                                          '52542')
        unassign()
        self.assertEqual(len(self.mock_remote.post_calls), 2)

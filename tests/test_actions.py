import unittest
from oscqam import actions, models


class UndoAction(actions.OscAction):
    def __init__(self):
        # Don't call super to prevent query to model objects.
        self.undo_stack = []
        self.undos = []

    def action(self):
        self.undo_stack.append(lambda: self.undos.append(1))
        raise models.RemoteError(None, None, None, None, None)


class ActionTests(unittest.TestCase):
    def test_undo(self):
        u = UndoAction()
        u()
        self.assertEqual(u.undos, [1])

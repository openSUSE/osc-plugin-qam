import os
import unittest
from oscqam import actions, models
from .utils import load_fixture
from .mockremote import MockRemote


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
        self.user_id = 'anonymous'
        self.cloud_open = '12345'
        self.non_open = '23456'
        self.sle_open = '34567'
        self.non_qam = '45678'
        self.assigned = '52542'
        self.multi_assign = 'twoassign'
        self.template = load_fixture('template.txt')

    def test_undo(self):
        u = UndoAction()
        u()
        self.assertEqual(u.undos, [1])

    def test_infer_no_groups_match(self):
        assign_action = actions.AssignAction(self.mock_remote, self.user_id,
                                             self.cloud_open)
        self.assertRaises(actions.NonMatchingGroupsError, assign_action)

    def test_infer_groups_match(self):
        assign_action = actions.AssignAction(self.mock_remote, self.user_id,
                                             self.sle_open)
        assign_action()
        self.assertEqual(len(self.mock_remote.post_calls), 1)

    def test_infer_groups_no_qam_reviews(self):
        assign_action = actions.AssignAction(self.mock_remote, self.user_id,
                                             self.non_qam)
        self.assertRaises(actions.NoQamReviewsError, assign_action)

    def test_unassign_explicit_group(self):
        unassign = actions.UnassignAction(self.mock_remote, self.user_id,
                                          self.non_open, 'qam-sle')
        unassign()
        self.assertEqual(len(self.mock_remote.post_calls), 2)

    def test_unassign_inferred_group(self):
        unassign = actions.UnassignAction(self.mock_remote, self.user_id,
                                          self.assigned)
        unassign()
        self.assertEqual(len(self.mock_remote.post_calls), 2)

    def test_unassign_no_group(self):
        unassign = actions.UnassignAction(self.mock_remote, self.user_id,
                                          self.non_qam)
        self.assertRaises(actions.NoReviewError, unassign)

    def test_unassign_multiple_groups(self):
        unassign = actions.UnassignAction(self.mock_remote, self.user_id,
                                          self.multi_assign)
        self.assertRaises(actions.MultipleReviewsError, unassign)

    def test_reject_not_failed(self):
        request = models.Request.by_id(self.mock_remote, self.cloud_open)
        template = models.Template(request,
                                   tr_getter=lambda x: self.template)
        action = actions.RejectAction(self.mock_remote, self.user_id,
                                      self.cloud_open)
        action._template = template
        self.assertRaises(actions.TestResultMismatchError, action)

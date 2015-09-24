import os
import StringIO
import unittest
from oscqam import actions, cli, models, fields
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
        self.one_assigned = '56789'
        self.assigned = '52542'
        self.single_assign_single_open = 'oneassignoneopen'
        self.two_assigned = 'twoassigned'
        self.multi_available_assign = 'twoqam'
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
                                             self.sle_open,
                                             template_factory = lambda r: True)
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

    def test_assign_non_matching_groups(self):
        assign = actions.AssignAction(self.mock_remote, self.user_id,
                                      self.single_assign_single_open,
                                      template_factory=lambda r: True)
        self.assertRaises(actions.NonMatchingGroupsError, assign)

    def test_assign_multiple_groups(self):
        assign = actions.AssignAction(self.mock_remote, self.user_id,
                                      self.multi_available_assign,
                                      template_factory=lambda r: True)
        self.assertRaises(actions.UninferableError, assign)

    def test_assign_multiple_groups_explicit(self):
        out = StringIO.StringIO()
        assign = actions.AssignAction(self.mock_remote, self.user_id,
                                      self.multi_available_assign,
                                      group = 'qam-test',
                                      template_factory = lambda r: True,
                                      out = out)
        assign()
        self.assertEqual(assign.out.getvalue(),
                         "Assigned Unknown User (anonymous@nowhere.none) "
                         "to qam-test for 56789.\n")

    def test_unassign_no_group(self):
        unassign = actions.UnassignAction(self.mock_remote, self.user_id,
                                          self.non_qam)
        self.assertRaises(actions.NoReviewError, unassign)

    def test_unassign_multiple_groups(self):
        unassign = actions.UnassignAction(self.mock_remote, self.user_id,
                                          self.two_assigned)
        self.assertRaises(actions.MultipleReviewsError, unassign)

    def test_reject_not_failed(self):
        request = models.Request.by_id(self.mock_remote, self.cloud_open)
        template = models.Template(request,
                                   tr_getter=lambda x: self.template)
        action = actions.RejectAction(self.mock_remote, self.user_id,
                                      self.cloud_open)
        action._template = template
        with self.assertRaises(models.TestResultMismatchError) as context:
            action()
        self.assertIn(models.Template.base_url, str(context.exception))

    def test_assign_no_report(self):
        def raiser(request):
            raise models.TemplateNotFoundError("")
        assign = actions.AssignAction(self.mock_remote, self.user_id,
                                      self.multi_available_assign,
                                      group = 'qam-test',
                                      template_factory = raiser)
        self.assertRaises(actions.ReportNotYetGeneratedError, assign)

    def test_assign_only_one_group(self):
        assign = actions.AssignAction(self.mock_remote, self.user_id,
                                      self.one_assigned, group='qam-test',
                                      template_factory=lambda r: True)
        self.assertRaises(actions.OneGroupAssignedError, assign)

    def test_list_assigned_user(self):
        self.mock_remote.register_url(
            'request', lambda: load_fixture('search_request.xml')
        )
        action = actions.ListAssignedUserAction(
            self.mock_remote, self.user_id, template_factory = lambda r: True
        )
        requests = action.load_requests()
        self.assertEqual(len(requests), 1)

    def test_list_assigned(self):
        action = actions.ListAssignedAction(self.mock_remote, 'anonymous',
                                            fields.DefaultFields())
        self.mock_remote.register_url('group',
                                      lambda: load_fixture('group_all.xml'))
        endpoint = ("/source/SUSE:Maintenance:130/_attribute/"
                    "OBS:IncidentPriority")
        self.mock_remote.register_url(
            endpoint,
            lambda: load_fixture("incident_priority.xml")
        )
        requests = action.load_requests()
        self.assertEqual(len(requests), 1)

    def test_approval_requires_testplanreviewer(self):
        request = models.Request.by_id(self.mock_remote, self.cloud_open)
        report = os.linesep.join(["SUMMARY: PASSED",
                                  "Test Plan Reviewer: "])
        template = models.Template(request,
                                   tr_getter = lambda x: report)
        approval = actions.ApproveAction(
            self.mock_remote, self.user_id, "12345",
            template_factory = lambda _: template
        )
        self.assertRaises(models.TestPlanReviewerNotSetError, approval)

    def test_approval_no_testplanreviewer_key(self):
        request = models.Request.by_id(self.mock_remote, self.cloud_open)
        report = "SUMMARY: PASSED"
        template = models.Template(request,
                                   tr_getter = lambda x: report)
        approval = actions.ApproveAction(
            self.mock_remote, self.user_id, "12345",
            template_factory = lambda _: template
        )
        self.assertRaises(models.TestPlanReviewerNotSetError, approval)

    def test_approval_requires_status_passed(self):
        request = models.Request.by_id(self.mock_remote, self.cloud_open)
        report = os.linesep.join(["SUMMARY: FAILED",
                                  "Test Plan Reviewer: someone"])
        template = models.Template(request,
                                   tr_getter = lambda x: report)
        approval = actions.ApproveAction(
            self.mock_remote, self.user_id, "12345",
            template_factory = lambda _: template
        )
        self.assertRaises(models.TestResultMismatchError, approval)

    def test_approval(self):
        request = models.Request.by_id(self.mock_remote, self.cloud_open)
        report = os.linesep.join(["SUMMARY: PASSED",
                                  "Test Plan Reviewer: someone"])
        template = models.Template(request,
                                   tr_getter = lambda x: report)
        approval = actions.ApproveAction(
            self.mock_remote, self.user_id, "12345",
            template_factory = lambda _: template
        )
        approval()
        self.assertEqual(len(self.mock_remote.post_calls), 1)

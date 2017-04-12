import os
import StringIO
import unittest
from oscqam import (actions, cli, errors, models, fields, remotes,
                    reject_reasons)
from .utils import load_fixture, create_template_data
from .mockremote import MockRemote


class UndoAction(actions.OscAction):
    def __init__(self):
        # Don't call super to prevent query to model objects.
        self.undo_stack = []
        self.undos = []

    def action(self):
        self.undo_stack.append(lambda: self.undos.append(1))
        raise remotes.RemoteError(None, None, None, None, None)


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
        self.rejected = 'request_rejected.xml'
        self.one_open = 'sletest'
        self.last_qam = 'approval_last_qam'
        self.inverse_assign_order = 'inverse_assign'
        self.template = load_fixture('template.txt')

    def test_undo(self):
        u = UndoAction()
        u()
        self.assertEqual(u.undos, [1])

    def test_infer_no_groups_match(self):
        assign_action = actions.AssignAction(self.mock_remote, self.user_id,
                                             self.cloud_open)
        self.assertRaises(errors.NonMatchingUserGroupsError, assign_action)

    def test_infer_groups_match(self):
        args = {'project': 'SUSE:Maintenance:130',
                'withfullhistory': '1',
                'view': 'collection'}
        self.mock_remote.register_url('request', lambda: "<request />", args)
        assign_action = actions.AssignAction(self.mock_remote, self.user_id,
                                             self.sle_open,
                                             template_factory = lambda r: True)
        assign_action()
        self.assertEqual(len(self.mock_remote.post_calls), 1)

    def test_infer_groups_no_qam_reviews(self):
        assign_action = actions.AssignAction(self.mock_remote, self.user_id,
                                             self.non_qam)
        self.assertRaises(errors.NoQamReviewsError, assign_action)

    def test_unassign_explicit_group(self):
        unassign = actions.UnassignAction(self.mock_remote, self.user_id,
                                          self.non_open, ['qam-test'])
        unassign()
        self.assertEqual(len(self.mock_remote.post_calls), 2)

    def test_unassign_inferred_group(self):
        unassign = actions.UnassignAction(self.mock_remote, self.user_id,
                                          self.assigned)
        unassign()
        self.assertEqual(len(self.mock_remote.post_calls), 2)

    def test_unassign_subset_group(self):
        out = StringIO.StringIO()
        unassign = actions.UnassignAction(self.mock_remote, self.user_id,
                                          self.two_assigned, ['qam-sle'],
                                          out = out)
        unassign()
        self.assertEqual(len(self.mock_remote.post_calls), 1)
        self.assertNotIn("Will close review for Unknown User "
                         "(anonymous@nowhere.none)", unassign.out.getvalue())

    def test_assign_non_matching_groups(self):
        assign = actions.AssignAction(self.mock_remote, self.user_id,
                                      self.single_assign_single_open,
                                      template_factory = lambda r: True)
        self.assertRaises(errors.NonMatchingUserGroupsError, assign)

    def test_assign_multiple_groups(self):
        assign = actions.AssignAction(self.mock_remote, self.user_id,
                                      self.multi_available_assign,
                                      template_factory = lambda r: True)
        self.assertRaises(errors.UninferableError, assign)

    def test_assign_multiple_groups_explicit(self):
        args = {'project': 'SUSE:Maintenance:130',
                'withfullhistory': '1',
                'view': 'collection'}
        self.mock_remote.register_url('request', lambda: "<request />", args)
        out = StringIO.StringIO()
        assign = actions.AssignAction(self.mock_remote, self.user_id,
                                      self.multi_available_assign,
                                      groups = ['qam-test'],
                                      template_factory = lambda r: True,
                                      out = out)
        assign()
        self.assertEqual(assign.out.getvalue(),
                         "Assigning Unknown User (anonymous@nowhere.none) "
                         "to qam-test for 56789.\n")

    def test_unassign_no_group(self):
        unassign = actions.UnassignAction(self.mock_remote, self.user_id,
                                          self.non_qam)
        self.assertRaises(errors.NoReviewError, unassign)

    def test_unassign_multiple_groups(self):
        out = StringIO.StringIO()
        unassign = actions.UnassignAction(self.mock_remote, self.user_id,
                                          self.two_assigned, out = out)
        unassign()
        self.assertIn("Unassigning Unknown User (anonymous@nowhere.none) "
                      "from twoassigned for group qam-sle",
                      unassign.out.getvalue())
        self.assertIn("Unassigning Unknown User (anonymous@nowhere.none) "
                      "from twoassigned for group qam-cloud",
                      unassign.out.getvalue())
        self.assertIn("Will close review for Unknown User "
                      "(anonymous@nowhere.none)", unassign.out.getvalue())

    def test_reject_not_failed(self):
        """Can not reject a request when the test report is not failed."""
        request = self.mock_remote.requests.by_id(self.cloud_open)
        template = models.Template(request,
                                   tr_getter = lambda x: self.template)
        action = actions.RejectAction(
            self.mock_remote, self.user_id,
            self.cloud_open,
            reject_reasons.RejectReason.administrative
        )
        action._template = template
        with self.assertRaises(errors.TestResultMismatchError) as context:
            action()
        self.assertIn(models.Template.base_url, str(context.exception))

    def test_reject_no_comment(self):
        """Can not reject a request when the test report is not failed."""
        request = self.mock_remote.requests.by_id(self.cloud_open)
        template = models.Template(
            request,
            tr_getter = lambda x: ("SUMMARY: FAILED"
                                   "\n"
                                   "comment: NONE"
                                   "\n"
                                   "\n"
                                   "Products: test")
        )
        action = actions.RejectAction(
            self.mock_remote, self.user_id,
            self.cloud_open,
            reject_reasons.RejectReason.administrative
        )
        action._template = template
        self.assertRaises(errors.NoCommentError, action)

    def test_reject_posts_reason(self):
        """Rejecting a request will post a reason attribute."""
        request = self.mock_remote.requests.by_id(self.cloud_open)
        template = models.Template(request,
                                   tr_getter = lambda x: """SUMMARY: FAILED

                                   comment: Something broke.""")
        endpoint = "source/{prj}/_attribute/MAINT:RejectReason".format(
            prj = request.src_project
        )
        self.mock_remote.register_url(
            endpoint,
            lambda: load_fixture('reject_reason_attribute.xml')
        )
        action = actions.RejectAction(
            self.mock_remote, self.user_id,
            self.cloud_open,
            [reject_reasons.RejectReason.administrative]
        )
        action._template = template
        action()
        self.assertEquals(len(self.mock_remote.post_calls), 2)
        self.assertIn(request.src_project, self.mock_remote.post_calls[0])

    def test_assign_no_report(self):
        def raiser(request):
            raise errors.TemplateNotFoundError("")
        assign = actions.AssignAction(self.mock_remote, self.user_id,
                                      self.multi_available_assign,
                                      groups = ['qam-test'],
                                      template_factory = raiser)
        self.assertRaises(errors.ReportNotYetGeneratedError, assign)

    def test_list_assigned_user(self):
        self.mock_remote.register_url(
            'request', lambda: load_fixture('search_request.xml'),
            {'states': 'new,review', 'user': 'anonymous',
             'view': 'collection', 'withfullhistory': '1'}
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
        request = self.mock_remote.requests.by_id(self.cloud_open)
        report = create_template_data(**{'SUMMARY': "PASSED",
                                         "Test Plan Reviewer": ""})
        template = models.Template(request,
                                   tr_getter = lambda x: report)
        approval = actions.ApproveUserAction(
            self.mock_remote, self.user_id, "12345", self.user_id,
            template_factory = lambda _: template
        )
        self.assertRaises(errors.TestPlanReviewerNotSetError, approval)

    def test_approval_no_testplanreviewer_key(self):
        request = self.mock_remote.requests.by_id(self.cloud_open)
        report = create_template_data(SUMMARY = "PASSED")
        template = models.Template(request,
                                   tr_getter = lambda x: report)
        approval = actions.ApproveUserAction(
            self.mock_remote, self.user_id, "12345", self.user_id,
            template_factory = lambda _: template
        )
        self.assertRaises(errors.TestPlanReviewerNotSetError, approval)

    def test_approval_requires_status_passed(self):
        request = self.mock_remote.requests.by_id(self.cloud_open)
        report = create_template_data(**{"SUMMARY": "FAILED",
                                         "Test Plan Reviewer": "someone"})
        template = models.Template(request,
                                   tr_getter = lambda x: report)
        approval = actions.ApproveUserAction(
            self.mock_remote, self.user_id, "12345", self.user_id,
            template_factory = lambda _: template
        )
        self.assertRaises(errors.TestResultMismatchError, approval)

    def test_approval(self):
        request = self.mock_remote.requests.by_id(self.cloud_open)
        report = create_template_data(**{"SUMMARY": "PASSED",
                                         "Test Plan Reviewer": "someone"})
        template = models.Template(request,
                                   tr_getter = lambda x: report)
        approval = actions.ApproveUserAction(
            self.mock_remote, self.user_id, "12345", self.user_id,
            template_factory = lambda _: template
        )
        approval()
        self.assertEqual(len(self.mock_remote.post_calls), 1)

    def test_report_field(self):
        self.assertEqual("Assigned Roles",
                         str(fields.ReportField.assigned_roles))
        self.assertEqual(fields.ReportField.assigned_roles,
                         fields.ReportField.from_str("Assigned Roles"))

    def test_load_requests_with_exception(self):
        def raise_template_not_found(self):
            raise errors.TemplateNotFoundError("Test error")
        request_1 = self.mock_remote.requests.by_id(self.cloud_open)
        request_2 = self.mock_remote.requests.by_id(self.non_open)
        request_2.get_template = raise_template_not_found
        action = actions.ListOpenAction(self.mock_remote, 'anonymous',
                                        template_factory = lambda r: r)
        requests = list(action._load_listdata([request_1, request_2]))
        self.assertEqual(1, len(requests))

    def test_remove_comment(self):
        action = actions.DeleteCommentAction(self.mock_remote,
                                             self.user_id,
                                             '0')
        action()
        self.assertEqual(len(self.mock_remote.delete_calls), 1)

    def test_assign_previous_reject_not_old_reviewer(self):
        self.mock_remote.register_url(
            'request',
            lambda: load_fixture(self.rejected),
            {'project': 'SUSE:Maintenance:130',
             'view': 'collection', 'withfullhistory': '1'},
        )
        assign = actions.AssignAction(self.mock_remote, 'anonymous2',
                                      self.multi_available_assign,
                                      groups = ['qam-test'],
                                      template_factory = lambda r: r)
        self.assertRaises(errors.NotPreviousReviewerError, assign)

    def test_assign_previous_reject_old_reviewer(self):
        out = StringIO.StringIO()
        self.mock_remote.register_url(
            'request',
            lambda: load_fixture(self.rejected),
            {'project': 'SUSE:Maintenance:130',
             'view': 'collection', 'withfullhistory': '1'},
        )
        assign = actions.AssignAction(self.mock_remote, 'anonymous',
                                      self.multi_available_assign,
                                      groups = ['qam-test'],
                                      template_factory = lambda r: r,
                                      out = out)
        assign()
        self.assertEqual(assign.out.getvalue(),
                         "Assigning Unknown User (anonymous@nowhere.none) "
                         "to qam-test for 56789.\n")

    def test_assign_previous_reject_not_old_reviewer_force(self):
        out = StringIO.StringIO()
        self.mock_remote.register_url(
            'request',
            lambda: load_fixture(self.rejected),
            {'project': 'SUSE:Maintenance:130',
             'view': 'collection', 'withfullhistory': '1'},
        )
        assign = actions.AssignAction(self.mock_remote, 'anonymous2',
                                      self.multi_available_assign,
                                      groups = ['qam-test'],
                                      template_factory = lambda r: r,
                                      force = True, out = out)
        assign()
        self.assertEqual(assign.out.getvalue(),
                         "Assigning Unknown User (anon2@nowhere.none) "
                         "to qam-test for 56789.\n")

    def test_assign_skip_template(self):
        """Assign a request without a testreport template."""
        out = StringIO.StringIO()
        self.mock_remote.register_url(
            'request',
            lambda: load_fixture(self.rejected),
            {'project': 'SUSE:Maintenance:130',
             'view': 'collection', 'withfullhistory': '1'},
        )
        def raiser(request):
            raise errors.TemplateNotFoundError("")
        assign = actions.AssignAction(self.mock_remote, self.user_id,
                                      self.multi_available_assign,
                                      groups = ['qam-test'],
                                      template_factory = raiser,
                                      out = out, template_required = False)
        assign()
        self.assertEqual(assign.out.getvalue(),
                         "Assigning Unknown User (anonymous@nowhere.none) "
                         "to qam-test for 56789.\n")

    def test_report(self):
        report = create_template_data(**{"SUMMARY": "PASSED",
                                         "Test Plan Reviewer": "someone"})
        request = self.mock_remote.requests.by_id(self.cloud_open)
        template = models.Template(request,
                                   tr_getter = lambda x: report)
        report = actions.Report(
            request = request,
            template_factory = lambda _: template
        )
        self.assertEqual(report.value(fields.ReportField.assigned_roles),
                         ["qam-sle -> Unknown User (anonymous@nowhere.none)"])
        self.assertEqual(report.value(fields.ReportField.package_streams),
                         ["update-test-trival.SUSE_SLE-12_Update"])
        self.assertEqual(report.value(fields.ReportField.unassigned_roles),
                         ['qam-cloud'])

    def test_unassign_permission_error(self):
        def raiser():
            raise remotes.RemoteError(None, None, None, None, None)
        out = StringIO.StringIO()
        self.mock_remote.register_url(
            'request/twoassigned?newstate=accepted&'
            'cmd=changereviewstate&by_user=anonymous',
            raiser,
            "[oscqam] Unassigning Unknown User (anonymous@nowhere.none) from "
            "twoassigned for group qam-cloud, qam-sle."
        )
        unassign = actions.UnassignAction(self.mock_remote, self.user_id,
                                          self.two_assigned, out = out)
        unassign()
        value = unassign.out.getvalue()
        self.assertIn("Unassigning Unknown User (anonymous@nowhere.none) "
                      "from twoassigned for group qam-sle",
                      value)
        self.assertIn("Unassigning Unknown User (anonymous@nowhere.none) "
                      "from twoassigned for group qam-cloud",
                      value)
        self.assertIn("Will close review for Unknown User "
                      "(anonymous@nowhere.none)", value)
        self.assertIn("UNDO: Undoing reopening of group qam-cloud", value)
        self.assertIn("UNDO: Undoing reopening of group qam-sle", value)

    def test_decline_output(self):
        out = StringIO.StringIO()
        request = self.mock_remote.requests.by_id(self.cloud_open)
        template = models.Template(request,
                                   tr_getter = lambda x: """SUMMARY: FAILED

                                   comment: Something broke.""")
        endpoint = "source/{prj}/_attribute/MAINT:RejectReason".format(
            prj = request.src_project
        )
        self.mock_remote.register_url(
            endpoint,
            lambda: load_fixture('reject_reason_attribute.xml')
        )
        action = actions.RejectAction(
            self.mock_remote, self.user_id,
            self.cloud_open,
            [reject_reasons.RejectReason.administrative],
            out = out
        )
        action._template = template
        action()
        self.assertIn(
            "Declining request {req} for {user}. See Testreport: {url}".format(
                req = request,
                user = action.user,
                url = action.template.url()
            ), action.out.getvalue())

    def test_approve_output(self):
        out = StringIO.StringIO()
        request = self.mock_remote.requests.by_id(self.cloud_open)
        report = create_template_data(**{"SUMMARY": "PASSED",
                                         "Test Plan Reviewer": "someone"})
        template = models.Template(request,
                                   tr_getter = lambda x: report)
        approval = actions.ApproveUserAction(
            self.mock_remote, self.user_id, "12345", self.user_id,
            template_factory = lambda _: template,
            out = out
        )
        approval()
        self.assertIn("Approving {req} for {user} ({group}). Testreport: {url}"
                      .format(
                          req = request,
                          user = approval.reviewer,
                          url = approval.template.url(),
                          group = 'qam-sle',
                      ), approval.out.getvalue())

    def test_approve_not_assigned(self):
        """A user can not approve an update that is not assigned to him."""
        unassigned_request = self.mock_remote.requests.by_id(
            self.multi_available_assign
        )
        report = create_template_data(**{"SUMMARY": "PASSED",
                                         "Test Plan Reviewer": "someone"})
        template = models.Template(unassigned_request,
                                   tr_getter = lambda x: report)
        approve_action = actions.ApproveUserAction(
            self.mock_remote,
            self.user_id,
            self.multi_available_assign,
            self.user_id,
            template_factory = lambda _: template
        )
        self.assertRaises(errors.NotAssignedError, approve_action)

    def test_approve_additional_groups(self):
        """If a user can handle more groups after an approval he will be notified
        about it.

        """
        out = StringIO.StringIO()
        request = self.mock_remote.requests.by_id(
            self.one_open,
        )
        report = create_template_data(**{"SUMMARY": "PASSED",
                                         "Test Plan Reviewer": "someone"})
        template = models.Template(request,
                                   tr_getter = lambda x: report)
        approval = actions.ApproveUserAction(
            self.mock_remote,
            self.user_id,
            self.one_open,
            self.user_id,
            template_factory = lambda _: template,
            out = out,
        )
        approval()
        self.assertIn("Approving {req} for {user} ({group}). Testreport: {url}"
                      .format(
                          req = request,
                          user = approval.reviewer,
                          url = approval.template.url(),
                          group = 'qam-sle',
                      ), approval.out.getvalue())
        self.assertIn("The following groups could also be reviewed by you: qam-test",
                      approval.out.getvalue())

    def test_approve_group(self):
        out = StringIO.StringIO()
        request = self.mock_remote.requests.by_id(
            self.one_open,
        )
        report = create_template_data(**{"SUMMARY": "PASSED",
                                         "Test Plan Reviewer": "someone"})
        template = models.Template(request,
                                   tr_getter = lambda x: report)
        approval = actions.ApproveGroupAction(
            self.mock_remote,
            self.user_id,
            self.one_open,
            'qam-test',
            template_factory = lambda _: template,
            out = out,
        )
        approval()
        self.assertIn("Approving {req} for group {group}."
                      .format(
                          req = request,
                          group = 'qam-test',
                      ), approval.out.getvalue())

    def test_approve_group_not_in_request(self):
        out = StringIO.StringIO()
        request = self.mock_remote.requests.by_id(
            self.one_open,
        )
        report = create_template_data(**{"SUMMARY": "PASSED",
                                         "Test Plan Reviewer": "someone"})
        template = models.Template(request,
                                   tr_getter = lambda x: report)
        approval = actions.ApproveGroupAction(
            self.mock_remote,
            self.user_id,
            self.one_open,
            'qam-cloud',
            template_factory = lambda _: template,
            out = out,
        )
        self.assertRaises(errors.NonMatchingGroupsError, approval)

    def test_approve_last_group_does_not_raise(self):
        out = StringIO.StringIO()
        request = self.mock_remote.requests.by_id(
            self.last_qam,
        )
        report = create_template_data(**{"SUMMARY": "PASSED",
                                         "Test Plan Reviewer": "someone"})
        template = models.Template(request,
                                   tr_getter = lambda x: report)
        approval = actions.ApproveUserAction(
            self.mock_remote,
            self.user_id,
            self.last_qam,
            self.user_id,
            template_factory = lambda _: template,
            out = out,
        )
        approval()
        self.assertIn("Approving {req} for {user} ({group}). Testreport: {url}"
                      .format(
                          req = request,
                          user = approval.reviewer,
                          url = approval.template.url(),
                          group = 'qam-sle',
                      ), approval.out.getvalue())

    def test_approve_misses_assigned_role(self):
        out = StringIO.StringIO()
        request = self.mock_remote.requests.by_id(
            self.inverse_assign_order,
        )
        report = create_template_data(**{"SUMMARY": "PASSED",
                                         "Test Plan Reviewer": "someone"})
        template = models.Template(request,
                                   tr_getter = lambda x: report)
        approval = actions.ApproveUserAction(
            self.mock_remote,
            self.user_id,
            self.inverse_assign_order,
            self.user_id,
            template_factory = lambda _: template,
            out = out,
        )
        approval()
        self.assertIn("Approving {req} for {user} ({group}). Testreport: {url}"
                      .format(
                          req = request,
                          user = approval.reviewer,
                          url = approval.template.url(),
                          group = 'qam-sle',
                      ), approval.out.getvalue())

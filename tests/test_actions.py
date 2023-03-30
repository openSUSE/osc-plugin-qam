from io import StringIO

import pytest

from oscqam import actions, errors, fields, models, reject_reasons, remotes
from oscqam.actions.oscaction import OscAction
from oscqam.actions.report import Report

from .utils import FakeTrGetter, create_template_data, load_fixture


class UndoAction(OscAction):
    def __init__(self):
        # Don't call super to prevent query to model objects.
        self.undo_stack = []
        self.undos = []

    def action(self):
        self.undo_stack.append(lambda: self.undos.append(1))
        raise remotes.RemoteError(None, None, None, None, None)


user_id = "anonymous"
cloud_open = "12345"
non_open = "23456"
sle_open = "34567"
non_qam = "45678"
one_assigned = "56789"
assigned = "52542"
single_assign_single_open = "oneassignoneopen"
two_assigned = "twoassigned"
multi_available_assign = "twoqam"
rejected = "request_rejected.xml"
one_open = "sletest"
last_qam = "approval_last_qam"
inverse_assign_order = "inverse_assign"
multireview = "multireview"
template_txt = load_fixture("template.txt")


def test_undo():
    u = UndoAction()
    u()
    assert u.undos == [1]


def test_infer_no_groups_match(remote):
    assign_action = actions.AssignAction(remote, user_id, cloud_open)
    with pytest.raises(errors.NonMatchingUserGroupsError):
        assign_action()


# TODO: Fix this
@pytest.mark.skip("Not implemented yet in mock")
def test_infer_groups_match(remote):
    args = {
        "project": "SUSE:Maintenance:130",
        "withfullhistory": "1",
        "view": "collection",
    }
    remote.register_url("request", lambda: "<request />", args)
    assign_action = actions.AssignAction(
        remote, user_id, sle_open, template_factory=lambda r: True
    )
    assign_action()
    assert len(remote.post_calls) == 1


def test_infer_groups_no_qam_reviews(remote):
    assign_action = actions.AssignAction(remote, user_id, non_qam)
    with pytest.raises(errors.NoQamReviewsError):
        assign_action()


def test_unassign_explicit_group(remote):
    unassign = actions.UnassignAction(remote, user_id, non_open, ["qam-test"])
    unassign()
    assert len(remote.post_calls) == 1


def test_unassign_multi_reviewer(remote):
    out = StringIO()
    unassign = actions.UnassignAction(
        remote, user_id, multireview, ["qam-sle"], out=out
    )
    unassign()
    assert (
        "Unassigning Unknown User (anonymous@nowhere.none) from 56789 for group qam-sle."
        in unassign.out.getvalue()
    )


def test_unassign_inferred_group(remote):
    unassign = actions.UnassignAction(remote, user_id, assigned)
    unassign()
    assert len(remote.post_calls) == 1


def test_unassign_subset_group(remote):
    out = StringIO()
    unassign = actions.UnassignAction(
        remote, user_id, two_assigned, ["qam-sle"], out=out
    )
    unassign()
    assert len(remote.post_calls) == 1
    assert (
        "Unassigning Unknown User (anonymous@nowhere.none) from twoassigned for group qam-sle"
        in unassign.out.getvalue()
    )


def test_assign_non_matching_groups(remote):
    assign = actions.AssignAction(
        remote, user_id, single_assign_single_open, template_factory=lambda r: True
    )
    with pytest.raises(errors.NonMatchingUserGroupsError):
        assign()


def test_assign_multiple_groups(remote):
    assign = actions.AssignAction(
        remote, user_id, multi_available_assign, template_factory=lambda r: True
    )
    with pytest.raises(errors.UninferableError):
        assign()


# TODO: Fix this
@pytest.mark.skip("Not implemented yet in mock")
def test_assign_multiple_groups_explicit(remote):
    args = {
        "project": "SUSE:Maintenance:130",
        "withfullhistory": "1",
        "view": "collection",
    }
    remote.register_url("request", lambda: "<request />", args)
    out = StringIO()
    assign = actions.AssignAction(
        remote,
        user_id,
        multi_available_assign,
        groups=["qam-test"],
        template_factory=lambda r: True,
        out=out,
    )
    assign()
    assert (
        assign.out.getvalue()
        == "Assigning Unknown User (anonymous@nowhere.none) to qam-test for 56789.\n"
    )


def test_unassign_no_group(remote):
    unassign = actions.UnassignAction(remote, user_id, non_qam)
    with pytest.raises(errors.NoReviewError):
        unassign()


def test_unassign_multiple_groups(remote):
    out = StringIO()
    unassign = actions.UnassignAction(remote, user_id, two_assigned, out=out)
    unassign()
    assert (
        "Unassigning Unknown User (anonymous@nowhere.none) from twoassigned for group qam-sle"
        in unassign.out.getvalue()
    )
    assert (
        "Unassigning Unknown User (anonymous@nowhere.none) from twoassigned for group qam-cloud"
        in unassign.out.getvalue()
    )


def test_reject_not_failed(remote):
    """Can not reject a request when the test report is not failed."""
    request = remote.requests.by_id(cloud_open)
    template = models.Template(request, tr_getter=FakeTrGetter(template_txt))
    action = actions.RejectAction(
        remote, user_id, cloud_open, [reject_reasons.RejectReason.administrative], False
    )
    action._template = template
    with pytest.raises(errors.TestResultMismatchError) as context:
        action()
    assert models.Template.base_url in str(context.value)


def test_reject_no_comment(remote):
    """Can not reject a request when the test report is not failed."""
    request = remote.requests.by_id(cloud_open)
    template = models.Template(
        request,
        tr_getter=FakeTrGetter(
            "SUMMARY: FAILED" "\n" "comment: NONE" "\n" "\n" "Products: test"
        ),
    )
    action = actions.RejectAction(
        remote, user_id, cloud_open, [reject_reasons.RejectReason.administrative], False
    )
    action._template = template
    with pytest.raises(errors.NoCommentError):
        action()


def test_reject_no_comment_force(remote):
    """Can not reject a request when the test report is not failed."""
    request = remote.requests.by_id(cloud_open)
    template = models.Template(
        request,
        tr_getter=FakeTrGetter(
            "SUMMARY: FAILED" "\n" "comment: NONE" "\n" "\n" "Products: test"
        ),
    )
    endpoint = "source/{prj}/_attribute/MAINT:RejectReason".format(
        prj=request.src_project
    )
    remote.register_url(endpoint, lambda: load_fixture("reject_reason_attribute.xml"))
    action = actions.RejectAction(
        remote, user_id, cloud_open, [reject_reasons.RejectReason.administrative], True
    )
    action._template = template
    action()
    assert len(remote.post_calls), 2
    assert request.src_project in remote.post_calls[0]


def test_reject_posts_reason(remote):
    """Rejecting a request will post a reason attribute."""
    request = remote.requests.by_id(cloud_open)
    template = models.Template(
        request,
        tr_getter=FakeTrGetter(
            """SUMMARY: FAILED

                               comment: Something broke.""",
        ),
    )
    endpoint = "source/{prj}/_attribute/MAINT:RejectReason".format(
        prj=request.src_project
    )
    remote.register_url(endpoint, lambda: load_fixture("reject_reason_attribute.xml"))
    action = actions.RejectAction(
        remote, user_id, cloud_open, [reject_reasons.RejectReason.administrative], False
    )
    action._template = template
    action()
    assert len(remote.post_calls), 2
    assert request.src_project in remote.post_calls[0]


def test_assign_no_report(remote):
    def raiser(request):
        raise errors.TemplateNotFoundError("")

    assign = actions.AssignAction(
        remote,
        user_id,
        multi_available_assign,
        groups=["qam-test"],
        template_factory=raiser,
    )
    with pytest.raises(errors.ReportNotYetGeneratedError):
        assign()


def test_assign_no_review(remote):
    assign = actions.AssignAction(
        remote,
        user_id,
        "rejected",
        groups=["qam-test"],
        template_factory=lambda r: True,
    )
    with pytest.raises(errors.NoQamReviewsError):
        assign()


# TODO: Fix this
@pytest.mark.skip("Not implemented yet in mock")
def test_list_assigned_user(remote):
    remote.register_url(
        "request",
        lambda: load_fixture("search_request.xml"),
        {
            "states": "new,review",
            "user": "anonymous",
            "view": "collection",
            "withfullhistory": "1",
        },
    )
    action = actions.ListAssignedUserAction(
        remote, user_id, template_factory=lambda r: True
    )
    requests = action.load_requests()
    assert len(requests) == 1


def test_list_assigned(remote):
    action = actions.ListAssignedAction(remote, "anonymous", fields.DefaultFields())
    remote.register_url("group", lambda: load_fixture("group_all.xml"))
    endpoint = "/source/SUSE:Maintenance:130/_attribute/" "OBS:IncidentPriority"
    remote.register_url(endpoint, lambda: load_fixture("incident_priority.xml"))
    requests = action.load_requests()
    assert len(requests) == 1


def test_approval_requires_status_passed(remote):
    request = remote.requests.by_id(cloud_open)
    report = create_template_data(
        **{
            "SUMMARY": "FAILED",
        }
    )
    template = models.Template(request, tr_getter=FakeTrGetter(report))
    approval = actions.ApproveUserAction(
        remote, user_id, "12345", user_id, template_factory=lambda _: template
    )
    with pytest.raises(errors.TestResultMismatchError):
        approval()


def test_approval(remote):
    request = remote.requests.by_id(cloud_open)
    report = create_template_data(
        **{
            "SUMMARY": "PASSED",
        }
    )
    template = models.Template(request, tr_getter=FakeTrGetter(report))
    approval = actions.ApproveUserAction(
        remote, user_id, "12345", user_id, template_factory=lambda _: template
    )
    approval()
    assert len(remote.post_calls) == 1


def test_report_field():
    assert "Assigned Roles" == str(fields.ReportField.assigned_roles)
    assert fields.ReportField.assigned_roles == fields.ReportField.from_str(
        "Assigned Roles"
    )


def test_load_requests_with_exception(remote):
    def raise_template_not_found(self):
        raise errors.TemplateNotFoundError("Test error")

    request_1 = remote.requests.by_id(cloud_open)
    request_2 = remote.requests.by_id(non_open)
    request_2.get_template = raise_template_not_found
    action = actions.ListOpenAction(remote, "anonymous", template_factory=lambda r: r)
    requests = list(action._load_listdata([request_1, request_2]))
    assert len(requests) == 1


def test_remove_comment(remote):
    action = actions.DeleteCommentAction(remote, user_id, "0")
    action()
    assert len(remote.delete_calls) == 1


def test_assign_previous_reject_not_old_reviewer(remote):
    remote.register_url(
        "request",
        lambda: load_fixture(rejected),
        {
            "project": "SUSE:Maintenance:130",
            "view": "collection",
            "withfullhistory": "1",
        },
    )
    assign = actions.AssignAction(
        remote,
        "anonymous2",
        multi_available_assign,
        groups=["qam-test"],
        template_factory=lambda r: r,
    )
    with pytest.raises(errors.NotPreviousReviewerError):
        assign()


# TODO: FIX thix
@pytest.mark.skip("Broken test - maybe wrong fixture")
def test_assign_previous_reject_old_reviewer(remote):
    out = StringIO()
    remote.register_url(
        "request",
        lambda: load_fixture(rejected),
        {
            "project": "SUSE:Maintenance:130",
            "view": "collection",
            "withfullhistory": "1",
        },
    )
    assign = actions.AssignAction(
        remote,
        "anonymous",
        multi_available_assign,
        groups=["qam-test"],
        template_factory=lambda r: r,
        out=out,
    )
    assign()
    assert (
        assign.out.getvalue()
        == "Assigning Unknown User (anonymous@nowhere.none) to qam-test for 56789.\n"
    )


def test_assign_previous_reject_not_old_reviewer_force(remote):
    out = StringIO()
    remote.register_url(
        "request",
        lambda: load_fixture(rejected),
        {
            "project": "SUSE:Maintenance:130",
            "view": "collection",
            "withfullhistory": "1",
        },
    )
    assign = actions.AssignAction(
        remote,
        "anonymous2",
        multi_available_assign,
        groups=["qam-test"],
        template_factory=lambda r: r,
        force=True,
        out=out,
    )
    assign()
    assert (
        assign.out.getvalue()
        == "Assigning Unknown User (anon2@nowhere.none) to qam-test for 56789.\n"
    )


# TODO: FIX thix
@pytest.mark.skip("Broken test - maybe wrong fixture")
def test_assign_skip_template(remote):
    """Assign a request without a testreport template."""
    out = StringIO()
    remote.register_url(
        "request",
        lambda: load_fixture(rejected),
        {
            "project": "SUSE:Maintenance:130",
            "view": "collection",
            "withfullhistory": "1",
        },
    )

    def raiser(request):
        raise errors.TemplateNotFoundError("")

    assign = actions.AssignAction(
        remote,
        user_id,
        multi_available_assign,
        groups=["qam-test"],
        template_factory=raiser,
        out=out,
        template_required=False,
    )
    assign()
    assert (
        assign.out.getvalue()
        == "Assigning Unknown User (anonymous@nowhere.none) to qam-test for 56789.\n"
    )


def test_report(remote):
    report = create_template_data(
        **{
            "SUMMARY": "PASSED",
        }
    )
    request = remote.requests.by_id(cloud_open)
    template = models.Template(request, tr_getter=FakeTrGetter(report))
    report = Report(request=request, template_factory=lambda _: template)
    assert report.value(fields.ReportField.assigned_roles) == [
        "qam-sle -> Unknown User (anonymous@nowhere.none)"
    ]
    assert report.value(fields.ReportField.package_streams) == [
        "update-test-trival.SUSE_SLE-12_Update"
    ]
    assert report.value(fields.ReportField.unassigned_roles) == ["qam-cloud"]


def test_unassign_permission_error(remote):
    def raiser():
        raise remotes.RemoteError(None, None, None, None, None)

    out = StringIO()
    remote.register_url(
        "request/twoassigned?newstate=accepted&"
        "cmd=changereviewstate&by_user=anonymous",
        raiser,
        "[oscqam] Unassigning Unknown User (anonymous@nowhere.none) from "
        "twoassigned for group qam-cloud, qam-sle.",
    )
    unassign = actions.UnassignAction(remote, user_id, two_assigned, out=out)
    unassign()
    value = unassign.out.getvalue()
    assert (
        "Unassigning Unknown User (anonymous@nowhere.none) from twoassigned for group qam-sle"
        in value
    )
    assert (
        "Unassigning Unknown User (anonymous@nowhere.none) from twoassigned for group qam-cloud"
        in value
    )


def test_decline_output(remote):
    out = StringIO()
    request = remote.requests.by_id(cloud_open)
    template = models.Template(
        request,
        tr_getter=FakeTrGetter(
            """SUMMARY: FAILED

                               comment: Something broke.""",
        ),
    )
    endpoint = "source/{prj}/_attribute/MAINT:RejectReason".format(
        prj=request.src_project
    )
    remote.register_url(endpoint, lambda: load_fixture("reject_reason_attribute.xml"))
    action = actions.RejectAction(
        remote,
        user_id,
        cloud_open,
        [reject_reasons.RejectReason.administrative],
        False,
        out=out,
    )
    action._template = template
    action()
    assert (
        "Declining request {req} for {user}. See Testreport: {url}".format(
            req=request, user=action.user, url=action.template.fancy_url
        )
        in action.out.getvalue()
    )


def test_approve_output(remote):
    out = StringIO()
    request = remote.requests.by_id(cloud_open)
    report = create_template_data(**{"SUMMARY": "PASSED"})
    template = models.Template(request, tr_getter=FakeTrGetter(report))
    approval = actions.ApproveUserAction(
        remote, user_id, "12345", user_id, template_factory=lambda _: template, out=out
    )
    approval()
    assert (
        "Approving {req} for {user} ({group}). Testreport: {url}\n".format(
            req=request,
            user=approval.reviewer,
            url=approval.template.fancy_url,
            group="qam-sle",
        )
        == approval.out.getvalue()
    )


def test_approve_not_assigned(remote):
    """A user can not approve an update that is not assigned to him."""
    unassigned_request = remote.requests.by_id(multi_available_assign)
    report = create_template_data(**{"SUMMARY": "PASSED"})
    template = models.Template(unassigned_request, tr_getter=FakeTrGetter(report))
    approve_action = actions.ApproveUserAction(
        remote,
        user_id,
        multi_available_assign,
        user_id,
        template_factory=lambda _: template,
    )
    with pytest.raises(errors.NotAssignedError):
        approve_action()


# TODO: FIX thix
@pytest.mark.skip("Broken test - maybe wrong fixture")
def test_approve_additional_groups(remote):
    """If a user can handle more groups after an approval he will be notified
    about it.

    """
    out = StringIO()
    request = remote.requests.by_id(
        one_open,
    )
    report = create_template_data(
        **{
            "SUMMARY": "PASSED",
        }
    )
    template = models.Template(request, tr_getter=FakeTrGetter(report))
    approval = actions.ApproveUserAction(
        remote,
        user_id,
        one_open,
        user_id,
        template_factory=lambda _: template,
        out=out,
    )
    approval()
    assert (
        "Approving {req} for {user} ({group}). Testreport: {url}\n".format(
            req=request,
            user=approval.reviewer,
            url=approval.template.fancy_url,
            group="qam-sle",
        )
        == approval.out.getvalue()
    )
    assert (
        "The following groups could also be reviewed by you: qam-test"
        in approval.out.getvalue()
    )


def test_approve_group(remote):
    out = StringIO()
    request = remote.requests.by_id(
        one_open,
    )
    report = create_template_data(
        **{
            "SUMMARY": "PASSED",
        }
    )
    template = models.Template(request, tr_getter=FakeTrGetter(report))
    approval = actions.ApproveGroupAction(
        remote,
        user_id,
        one_open,
        "qam-test",
        template_factory=lambda _: template,
        out=out,
    )
    approval()
    assert (
        "Approving {req} for group {group}.".format(req=request, group="qam-test")
        in approval.out.getvalue()
    )


def test_approve_group_not_in_request(remote):
    out = StringIO()
    request = remote.requests.by_id(
        one_open,
    )
    report = create_template_data(
        **{
            "SUMMARY": "PASSED",
        }
    )
    template = models.Template(request, tr_getter=FakeTrGetter(report))
    approval = actions.ApproveGroupAction(
        remote,
        user_id,
        one_open,
        "qam-cloud",
        template_factory=lambda _: template,
        out=out,
    )
    with pytest.raises(errors.NonMatchingGroupsError):
        approval()


def test_approve_last_group_does_not_raise(remote):
    out = StringIO()
    request = remote.requests.by_id(
        last_qam,
    )
    report = create_template_data(
        **{
            "SUMMARY": "PASSED",
        }
    )
    template = models.Template(request, tr_getter=FakeTrGetter(report))
    approval = actions.ApproveUserAction(
        remote,
        user_id,
        last_qam,
        user_id,
        template_factory=lambda _: template,
        out=out,
    )
    approval()
    assert (
        "Approving {req} for {user} ({group}). Testreport: {url}".format(
            req=request,
            user=approval.reviewer,
            url=approval.template.fancy_url,
            group="qam-sle",
        )
        in approval.out.getvalue()
    )


def test_approve_misses_assigned_role(remote):
    out = StringIO()
    request = remote.requests.by_id(
        inverse_assign_order,
    )
    report = create_template_data(
        **{
            "SUMMARY": "PASSED",
        }
    )
    template = models.Template(request, tr_getter=FakeTrGetter(report))
    approval = actions.ApproveUserAction(
        remote,
        user_id,
        inverse_assign_order,
        user_id,
        template_factory=lambda _: template,
        out=out,
    )
    approval()
    assert (
        "Approving {req} for {user} ({group}). Testreport: {url}".format(
            req=request,
            user=approval.reviewer,
            url=approval.template.fancy_url,
            group="qam-sle",
        )
        in approval.out.getvalue()
    )

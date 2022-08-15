from io import StringIO
from urllib.error import HTTPError

import osc
import pytest
import responses

from oscqam.domains import Priority, UnknownPriority
from oscqam.errors import MissingSourceProjectError
from oscqam.models import (
    Assignment,
    Attribute,
    Bug,
    Comment,
    Group,
    Request,
    Template,
    User,
)
from oscqam.reject_reasons import RejectReason

from .mockremote import MockRemote
from .utils import FakeTrGetter, create_template_data, load_fixture


comment_1_xml = load_fixture("comments_1.xml")
req_1_xml = load_fixture("request_12345.xml")
req_2_xml = load_fixture("request_23456.xml")
req_3_xml = load_fixture("request_52542.xml")
req_4_xml = load_fixture("request_56789.xml")
req_search = load_fixture("request_search.xml")
req_search_none = load_fixture("request_search_none_proj.xml")
req_no_src = load_fixture("request_no_src.xml")
req_assign = load_fixture("request_assign.xml")
req_unassign = load_fixture("request_unassign.xml")
req_unassigned = load_fixture("request_unassigned.xml")
req_invalid = load_fixture("request_no_src.xml")
req_sle11sp4 = load_fixture("request_sle11sp4.xml")
req_qam_auto = load_fixture("request_qam_auto.xml")
req_two_assign = load_fixture("request_twoassign.xml")
template_txt = load_fixture("template.txt")
template_rh = load_fixture("template_rh.txt")
user_txt = load_fixture("person_anonymous.xml")
group_txt = load_fixture("group_qam-sle.xml")
bugs_txt = load_fixture("bug_patchinfo.xml")


def create_template(request_data=None, template_data=None):
    if not request_data:
        request_data = req_1_xml
    if not template_data:
        template_data = template_txt
    request = Request.parse(MockRemote(), request_data)[0]
    template = Template(request, tr_getter=FakeTrGetter(template_data))
    return template


def test_merge_requests(remote):
    request_1 = Request.parse(remote, req_1_xml)[0]
    request_2 = Request.parse(remote, req_1_xml)[0]
    requests = set([request_1, request_2])
    assert len(requests) == 1


def test_search(remote):
    """Only requests that are part of SUSE:Maintenance projects should be
    used.
    """
    requests = Request.parse(remote, req_search)
    assert len(requests) == 2
    requests = Request.filter_by_project("SUSE:Maintenance", requests)
    assert len(requests) == 1


def test_search_empty_source_project(remote):
    """Projects with empty source project should be handled gracefully."""
    requests = Request.parse(remote, req_search_none)
    requests = Request.filter_by_project("SUSE:Maintenance", requests)
    assert len(requests) == 0


def test_project_without_source_project(remote):
    """When project attribute can be found in a source tag the API should
    just return an empty string and not fail.
    """
    requests = Request.parse(remote, req_no_src)
    assert requests[0].src_project == ""
    requests = Request.filter_by_project("SUSE:Maintenance", requests)
    assert len(requests) == 0


def test_assigned_roles_request(remote):
    request = Request.parse(remote, req_assign)[0]
    assigned = request.assigned_roles
    assert len(assigned) == 1
    assert assigned[0].user.login == "anonymous"
    assert assigned[0].group.name == "qam-sle"
    request = Request.parse(remote, req_3_xml)[0]
    assigned = request.assigned_roles
    assert len(assigned) == 1
    assert assigned[0].user.login == "anonymous"
    assert assigned[0].group.name == "qam-sle"


def test_assigned_multiple_roles(remote):
    request = Request.parse(remote, req_two_assign)[0]
    assigned = request.assigned_roles
    assert len(assigned) == 2
    groups = [a.group.name for a in assigned]
    logins = [a.user.login for a in assigned]
    assert "anonymous" in logins
    assert "qam-sle" in groups
    assert "qam-cloud" in groups


def test_assigned_roles_sle11_sp4(remote):
    request = Request.parse(remote, req_sle11sp4)[0]
    assigned = request.assigned_roles
    assert len(assigned) == 1
    assert assigned[0].user.login == "anonymous"
    assert assigned[0].group.name == "qam-sle"


def test_unassigned_removes_roles(remote):
    request = Request.parse(remote, req_unassign)[0]
    assigned = request.assigned_roles
    assert len(assigned) == 0


def test_parse_request_id():
    test_id = "SUSE:Maintenance:123:45678"
    req_id = Request.parse_request_id(test_id)
    assert req_id == "45678"


def test_template_splits_srcrpms():
    assert create_template().log_entries["SRCRPMs"] == ["glibc", "glibc-devel"]


def test_template_splits_bugs():
    template_data = create_template_data(Bugs="100001, 100002, 100003")
    assert create_template(template_data=template_data).log_entries["Bugs"] == [
        "100001",
        "100002",
        "100003",
    ]


def test_template_splits_products():
    assert create_template().log_entries["Products"] == [
        "SERVER 11-SP3 (i386, ia64, ppc64, s390x, x86_64)",
        "DESKTOP 11-SP3 (i386, x86_64)",
    ]


def test_template_splits_non_sle_products():
    assert create_template(template_data=template_rh).log_entries["Products"] == [
        "RHEL-TEST (i386)",
        "SERVER 11-SP3 (i386, ia64, ppc64, s390x, x86_64)",
    ]


def test_replacing_sle_prefix():
    template_data = create_template_data(Products="SLE-PSLE-SP3 (i386)")
    assert create_template(template_data=template_data).log_entries["Products"] == [
        "PSLE-SP3 (i386)"
    ]


def test_multi_line_comment():
    template_data = create_template_data(comment="A comment\nwith multiple lines")
    assert (
        create_template(template_data=template_data).log_entries["comment"]
        == "A comment\nwith multiple lines"
    )


def test_template_key_repeats():
    template_data = "\n".join(
        [
            "comment: a",
            "$Author: b",
            "Products: b",
            "Testplatform: base=sles",
            "Testplatform: base=studio",
        ]
    )
    assert (
        create_template(template_data=template_data).log_entries["Testplatform"]
        == "base=sles\nbase=studio"
    )


def test_multi_line_comment_first_line_empty():
    template_data = create_template_data(comment="\nwith multiple lines")
    assert (
        create_template(template_data=template_data).log_entries["comment"]
        == "with multiple lines"
    )


def test_multi_line_comment_with_header_seperator():
    template_data = create_template_data(comment="\nwith: multiple lines")
    assert (
        create_template(template_data=template_data).log_entries["comment"]
        == "with: multiple lines"
    )


def test_template_for_invalid_request(remote):
    request = Request.parse(remote, req_invalid)[0]
    with pytest.raises(MissingSourceProjectError):
        request.get_template(Template)


def test_assignment_equality(remote):
    user = User.parse(remote, user_txt)[0]
    group = Group.parse(remote, group_txt)[0]
    a1 = Assignment(user, group)
    a2 = Assignment(user, group)
    assert a1 == a2


def test_assignment_inference_single_group(remote):
    """Test that assignments can be inferred from a single group even
    if the comments are not used.
    """
    request = Request.parse(remote, req_4_xml)[0]
    assignments = Assignment.infer(remote, request)
    assert len(assignments) == 1
    assignment = assignments[0]
    assert assignment.user.login == "anonymous"
    assert assignment.group.name == "qam-sle"


def test_assignment_inference_ignores_qam_auto(remote):
    request = Request.parse(remote, req_4_xml)[0]
    assignments = Assignment.infer(remote, request)
    assert len(assignments) == 1
    assignment = assignments[0]
    assert assignment.user.login == "anonymous"
    assert assignment.group.name == "qam-sle"


@responses.activate
def test_incident_priority(remote):
    request = Request.parse(remote, req_1_xml)[0]
    src_project = request.src_project
    endpoint = "/source/{0}/_attribute/OBS:IncidentPriority".format(src_project)
    remote.register_url(
        endpoint,
        lambda: (
            "<attributes>"
            "<attribute name='IncidentPriority' namespace='OBS'>"
            "<value>100</value>"
            "</attribute>"
            "</attributes>"
        ),
    )
    incident_priority = request.incident_priority
    assert incident_priority == Priority(100)


@responses.activate
def test_incident_priority_empty(remote):
    request = Request.parse(remote, req_1_xml)[0]
    src_project = request.src_project
    endpoint = "/source/{0}/_attribute/OBS:IncidentPriority".format(src_project)
    remote.register_url(endpoint, lambda: "<attributes/>")
    incident_priority = request.incident_priority
    assert incident_priority == UnknownPriority()


@responses.activate
def test_no_incident_priority(remote):
    def raise_http():
        raise HTTPError("test", 500, "test", "", StringIO(""))

    request = Request.parse(remote, req_1_xml)[0]
    src_project = request.src_project
    endpoint = "/source/{0}/_attribute/OBS:IncidentPriority".format(src_project)
    remote.register_url(endpoint, raise_http)
    request = Request.parse(remote, req_1_xml)[0]
    assert request.incident_priority == UnknownPriority()


def test_priority_str():
    priority = UnknownPriority()
    assert "None" == str(priority)
    priority = Priority(100)
    assert "100" == str(priority)


def test_unassigned_roles(remote):
    request = Request.parse(remote, req_unassigned)[0]
    open_reviews = request.review_list_open()
    assert len(open_reviews) == 2
    assert open_reviews[0].reviewer.name == "qam-cloud"
    assert open_reviews[1].reviewer.name == "qam-sle"


def test_obs27_workaround_pre_152(remote):
    def raise_wrong_args(self, request):
        raise osc.oscerr.WrongArgs("acceptinfo")

    original_version = osc.core.get_osc_version
    original_read = Request.read
    osc.core.get_osc_version = lambda: "0.151"
    Request.read = raise_wrong_args
    try:
        request = Request.parse(remote, req_unassigned)
        assert request == []
    finally:
        Request.read = original_read
        osc.core.get_osc_version = original_version


def test_obs27_workaround_post_152(remote):
    def raise_wrong_args(self, request):
        raise osc.oscerr.WrongArgs("acceptinfo")

    original_read = Request.read
    Request.read = raise_wrong_args
    try:
        with pytest.raises(osc.oscerr.WrongArgs):
            Request.parse(remote, req_unassigned)
    finally:
        Request.read = original_read


def test_request_str(remote):
    request = Request.parse(remote, req_1_xml)[0]
    assert str(request) == "12345"


def test_parse_comment(remote):
    comment = Comment.parse(remote, comment_1_xml)[0]
    assert comment.id == "1322"
    assert comment.who == "anonymous"
    assert comment.text == "test comment - please remove"


def test_parse_empty_comment(remote):
    comment_data = '<comments request="0"/>'
    comments = Comment.parse(remote, comment_data)
    assert [] == comments


def test_attribute_parsing(remote):
    attribute = Attribute.parse(remote, load_fixture("reject_reason_attribute.xml"))[0]
    assert attribute.value == ["12345:abc", "23456:def"]


def test_attribute_writing(remote):
    attribute = Attribute.parse(remote, load_fixture("reject_reason_attribute.xml"))[0]
    assert (
        attribute.xml()
        == b'<attribute name="RejectReason" namespace="MAINT"><value>12345:abc</value><value>23456:def</value></attribute>'
    )


def test_attribute_get(remote):
    request = Request.parse(remote, req_1_xml)[0]
    endpoint = "source/{prj}/_attribute/MAINT:RejectReason".format(
        prj=request.src_project
    )
    attribute = Attribute.parse(remote, load_fixture("reject_reason_attribute.xml"))[0]
    remote.register_url(endpoint, lambda: load_fixture("reject_reason_attribute.xml"))
    assert attribute == request.attribute("MAINT:RejectReason")


def test_attribute_post(remote):
    reject = Attribute.preset(remote, Attribute.reject_reason, "Some_Value")
    remote.projects.set_attribute("oscqam:test", reject)
    assert len(remote.post_calls) == 1


def test_build_reject_reason(remote):
    request = Request.parse(remote, req_1_xml)[0]
    endpoint = "source/{prj}/_attribute/MAINT:RejectReason".format(
        prj=request.src_project
    )
    remote.register_url(
        endpoint, lambda: load_fixture("reject_reason_attribute_empty.xml")
    )
    reject_reasons = [RejectReason.administrative, RejectReason.build_problem]
    attribute = request._build_reject_attribute(reject_reasons)
    value1 = "{reqid}:{admin}".format(
        reqid=request.reqid, admin=RejectReason.administrative.flag
    )
    value2 = "{reqid}:{build}".format(
        reqid=request.reqid, build=RejectReason.build_problem.flag
    )
    assert attribute.value == (value1, value2)


def test_build_reject_reason_existing_reason(remote):
    request = Request.parse(remote, req_1_xml)[0]
    endpoint = "source/{prj}/_attribute/MAINT:RejectReason".format(
        prj=request.src_project
    )
    remote.register_url(endpoint, lambda: load_fixture("reject_reason_tracking.xml"))
    reject_reasons = [RejectReason.build_problem]
    attribute = request._build_reject_attribute(reject_reasons)
    value1 = "{reqid}:{track}".format(
        reqid=request.reqid, track=RejectReason.tracking_issue.flag
    )
    value2 = "{reqid}:{build}".format(
        reqid=request.reqid, build=RejectReason.build_problem.flag
    )
    assert attribute.value == [value1, value2]


def test_build_reject_reason_existing_reasons(remote):
    request = Request.parse(remote, req_1_xml)[0]
    endpoint = "source/{prj}/_attribute/MAINT:RejectReason".format(
        prj=request.src_project
    )
    remote.register_url(endpoint, lambda: load_fixture("reject_reason_attribute.xml"))
    reject_reasons = [RejectReason.build_problem]
    attribute = request._build_reject_attribute(reject_reasons)
    value2 = "{reqid}:{build}".format(
        reqid=request.reqid, build=RejectReason.build_problem.flag
    )
    assert attribute.value == ["12345:abc", "23456:def", value2]


def test_parse_bugs(remote):
    bugs = Bug.parse(remote, bugs_txt, "issue")
    assert len(bugs) == 4

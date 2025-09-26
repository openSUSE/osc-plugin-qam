"""Provides a wrapper around the osc request object."""

import logging
import re
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

import osc.core
import osc.oscerr

from ..errors import MissingSourceProjectError
from .assignment import Assignment
from .attribute import Attribute
from .comment import Comment
from .review import GroupReview, UserReview
from .xmlfactorymixin import XmlFactoryMixin


class Request(osc.core.Request, XmlFactoryMixin):
    """Wrapper around osc request object to add logic required by the
    qam-plugin.

    Attributes:
        STATE_NEW: A string representing the new state of a request.
        STATE_REVIEW: A string representing the review state of a request.
        STATE_DECLINED: A string representing the declined state of a request.
        OPEN_STATES: A list of states that are considered open.
        REVIEW_USER: A string representing a review by user.
        REVIEW_GROUP: A string representing a review by group.
        REVIEW_OTHER: A string representing a review by other.
        COMPLETE_REQUEST_ID_SRE: A compiled regular expression to extract the
            request ID from a string.
        COMPLETE_REQUEST_ID_SRE_PI: A compiled regular expression to extract the
            request ID from a string for PI requests.
        remote: A remote facade.
    """

    STATE_NEW = "new"
    STATE_REVIEW = "review"
    STATE_DECLINED = "declined"
    OPEN_STATES = [STATE_NEW, STATE_REVIEW]
    REVIEW_USER = "BY_USER"
    REVIEW_GROUP = "BY_GROUP"
    REVIEW_OTHER = "BY_OTHER"
    COMPLETE_REQUEST_ID_SRE = re.compile(r"(open)?SUSE:Maintenance:\d+:(?P<req>\d+)")
    COMPLETE_REQUEST_ID_SRE_PI = re.compile(r"(open)?SUSE:PI:.+:(?P<req>\d+)")

    def __init__(self, remote):
        """Initializes a Request.

        Args:
            remote: A remote facade.
        """
        self.remote = remote
        super().__init__()
        self._comments = None
        self._groups = None
        self._packages = None
        self._assigned_roles = None
        self._priority = None
        self._reviews = []
        self._attributes = {}
        self._issues = []
        self._incident = None

    def active(self):
        """Checks if the request is active.

        Returns:
            True if the request is in an active state, False otherwise.
        """
        return self.state == "new" or self.state == "review"

    @property
    def incident_priority(self):
        """The priority of the incident associated with the request."""
        if not self._priority:
            self._priority = self.remote.priorities.for_request(self)
        return self._priority

    @property
    def incident(self):
        """The incident ID of the request."""
        if not self._incident:
            self._incident = self.src_project.split(":")[-1]
        return self._incident

    @property
    def assigned_roles(self):
        """A list of assignments for the request."""
        if not self._assigned_roles:
            self._assigned_roles = Assignment.infer(self.remote, self)
        return self._assigned_roles

    @property
    def comments(self):
        """A list of comments for the request."""
        if not self._comments:
            self._comments = self.remote.comments.for_request(self) or [Comment.none]
        return self._comments

    @property
    def maker(self):
        """The user who created the request."""
        for history in self.statehistory:
            if history.description == "Request created":
                self._creator = self.remote.users.by_name(history.who)
                break
        else:
            self._creator = "Unknown"
        return self._creator

    @property
    def issues(self):
        """Bugs that should be fixed as part of this request."""
        if not self._issues:
            self._issues = self.remote.bugs.for_request(self)
        return self._issues

    @property
    def groups(self):
        """A list of groups associated with the request."""
        # Maybe use a invalidating cache as a trade-off between current
        # information and slow response.
        return [
            review.reviewer
            for review in self.review_list()
            if isinstance(review, GroupReview)
        ]

    @property
    def packages(self):
        """Collects all packages of the actions that are part of the request."""
        if not self._packages:
            packages = set()
            for action in self.actions:
                pkg = action.src_package
                if pkg != "patchinfo":
                    packages.add(pkg)
            self._packages = packages
        return self._packages

    @property
    def src_project(self):
        """Will return the src_project or an empty string if no src_project
        can be found in the request.

        Returns:
            The source project name.
        """
        for action in self.actions:
            if hasattr(action, "src_project"):
                prj = action.src_project
                if prj:
                    return prj
                else:
                    logging.info("This project has no source project: %s", self.reqid)
                    return ""
        return ""

    @property
    def src_project_to_rrid(self):
        """Will return the src_project or an empty string if no src_project
        can be found in the request.

        This is a special version for requests that are submitted to a
        staging project first.

        Returns:
            The source project name for the PI request.
        """
        for action in self.actions:
            if hasattr(action, "src_project"):
                prj = action.src_project
                if prj:
                    if prj.startswith("SUSE:SLFO:"):
                        ver = prj.split(":")[-2]
                        return f"SUSE:PI:{ver}"
                    return prj
                else:
                    logging.info("This project has no source project: %s", self.reqid)
                    return ""
        return ""

    def attribute(self, attribute):
        """Load the specified attribute for this request.

        As requests right now can not contain attributes the attribute will be
        loaded from the corresponding source-project.

        Args:
            attribute: The attribute to load.

        Returns:
            The value of the attribute.
        """
        if attribute not in self._attributes:
            attributes = self.remote.projects.get_attribute(self.src_project, attribute)
            if len(attributes) == 1:
                attributes = attributes[0]
            self._attributes[attribute] = attributes
        return self._attributes[attribute]

    def review_action(self, params, user=None, group=None, comment=None):
        """Performs a review action.

        Args:
            params: A dictionary of parameters for the action.
            user: The user performing the action.
            group: The group the action is for.
            comment: A comment to add to the action.

        Raises:
            AttributeError: If neither user nor group is specified.
        """
        if not user and not group:
            raise AttributeError("group or user required for this action.")
        if user:
            params["by_user"] = user.login
        if group:
            params["by_group"] = group.name
        url_params = urlencode(params)
        url = "/".join([self.remote.requests.endpoint, self.reqid])
        url += "?" + url_params
        self.remote.post(url, comment)

    def review_assign(self, group, reviewer, comment=None):
        """Assigns a review to a user.

        Args:
            group: The group to assign the review for.
            reviewer: The user to assign the review to.
            comment: A comment to add to the assignment.
        """
        params = {"cmd": "assignreview", "reviewer": reviewer.login}
        self.review_action(params, group=group, comment=comment)

    def review_unassign(self, group, reviewer, comment=None):
        """Will undo the assignment by the group

        Args:
            group: The group to unassign the review for.
            reviewer: The user to unassign the review from.
            comment: A comment to add to the unassignment.
        """
        params = {"cmd": "assignreview", "revert": 1, "reviewer": reviewer.login}
        self.review_action(params, group=group, comment=comment)

    def review_accept(self, user=None, group=None, comment=None):
        """Accepts a review.

        Args:
            user: The user accepting the review.
            group: The group the review is for.
            comment: A comment to add to the acceptance.
        """
        comment = self._format_review_comment(comment)
        params = {"cmd": "changereviewstate", "newstate": "accepted"}
        self.review_action(params, user, group, comment)

    def review_add(self, user=None, group=None, comment=None):
        """Will add a new reviewrequest for the given user or group.

        Args:
            user: The user to add the review for.
            group: The group to add the review for.
            comment: A comment to add to the review.
        """
        comment = self._format_review_comment(comment)
        params = {"cmd": "addreview"}
        self.review_action(params, user, group, comment)

    def review_decline(self, user=None, group=None, comment=None, reasons=None):
        """Will decline the reviewrequest for the given user or group.

        Args:
            user: The user declining the request.
            group: The group the request should be declined for.
            comment: A comment that will be added to describe why the
                request was declined.
            reasons: A list of RejectReason objects that
                explains why the request was declined.
                The reason will be added as an attribute to the Maintenance
                incident.
        """
        if reasons:
            reason = self._build_reject_attribute(reasons)
            self.remote.projects.set_attribute(self.src_project, reason)
        comment = self._format_review_comment(comment)
        params = {"cmd": "changereviewstate", "newstate": "declined"}
        self.review_action(params, user, group, comment)

    def _build_reject_attribute(self, reasons):
        """Builds a reject attribute from a list of reasons.

        Args:
            reasons: A list of RejectReason objects.

        Returns:
            An Attribute object.
        """
        reject_reason = self.attribute(Attribute.reject_reason)
        reason_values = list(
            map(lambda reason: "{0}:{1}".format(self.reqid, reason.flag), reasons)
        )
        if not reject_reason:
            reject_reason = Attribute.preset(
                self.remote, Attribute.reject_reason, *reason_values
            )
        else:
            for r in reason_values:
                reject_reason.value.append(r)
        return reject_reason

    def review_reopen(self, user=None, group=None, comment=None):
        """Will reopen a reviewrequest for the given user or group.

        Args:
            user: The user to reopen the review for.
            group: The group to reopen the review for.
            comment: A comment to add to the reopen.
        """
        params = {"cmd": "changereviewstate", "newstate": "new"}
        self.review_action(params, user, group, comment)

    def _format_review_comment(self, comment):
        """Formats a review comment.

        Args:
            comment: The comment to format.

        Returns:
            The formatted comment, or None if the comment is empty.
        """
        if not comment:
            return None
        return "[oscqam] {comment}".format(comment=comment)

    def review_list(self):
        """Returns all reviews as a list.

        Returns:
            A list of Review objects.
        """
        if not self._reviews:
            for review in self.reviews:
                if review.by_group:
                    self._reviews.append(GroupReview(self.remote, review))
                elif review.by_user:
                    self._reviews.append(UserReview(self.remote, review))
        return self._reviews

    def review_list_open(self):
        """Return only open reviews.

        Returns:
            A list of open Review objects.
        """
        return [r for r in self.review_list() if r.state in Request.OPEN_STATES]

    def review_list_accepted(self):
        """Returns a list of accepted reviews.

        Returns:
            A list of accepted Review objects.
        """
        return [r for r in self.review_list() if r.state.lower() == "accepted"]

    def add_comment(self, comment):
        """Adds a comment to this request.

        Args:
            comment: The comment to add.
        """
        endpoint = "/comments/request/{id}".format(id=self.reqid)
        self.remote.post(endpoint, comment)

    def get_template(self, template_factory):
        """Return the template associated with this request.

        Args:
            template_factory: A function to create a template.

        Returns:
            A Template object.

        Raises:
            MissingSourceProjectError: If the request has no source project.
        """
        if not self.src_project:
            raise MissingSourceProjectError(self)
        return template_factory(self)

    @classmethod
    def filter_by_project(cls, request_substring, requests):
        """Filters a list of requests by source project.

        Args:
            request_substring: The substring to search for in the source project.
            requests: A list of requests to filter.

        Returns:
            A list of requests that match the filter.
        """
        return [r for r in requests if request_substring in r.src_project]

    @classmethod
    def parse(cls, remote, xml):
        """Parses a list of requests from XML.

        Args:
            remote: A remote facade.
            xml: The XML to parse.

        Returns:
            A list of Request objects.
        """
        et = ET.fromstring(xml)
        requests = []
        for request in et.iter(remote.requests.endpoint):
            try:
                req = Request(remote)
                req.read(request)
                requests.append(req)
            except osc.oscerr.APIError as e:
                logging.error(e.msg)
                pass
            except osc.oscerr.WrongArgs as e:
                # Temporary workaround, as OBS >= 2.7 can return requests with
                # acceptinfo-elements that old osc can not handle.
                if not (osc.core.get_osc_version() < "0.152"):
                    raise
                if "acceptinfo" not in str(e):
                    raise
                else:
                    logging.error("Server version too high for osc-client: %s" % str(e))
                    pass
        return requests

    @classmethod
    def parse_request_id(cls, request_id):
        """Extract the request_id from a string if required.

        The method will extract the request-id of a complete request string
        (e.g. SUSE:Maintenance:123:45678 has a request id of 45678) if
        needed.

        Args:
            request_id: The string to parse the request ID from.

        Returns:
            The request ID.
        """
        reqid = cls.COMPLETE_REQUEST_ID_SRE.match(request_id)
        if reqid:
            return reqid.group("req")
        reqid = cls.COMPLETE_REQUEST_ID_SRE_PI.match(request_id)
        if reqid:
            return reqid.group("req")
        return request_id

    def __eq__(self, other):
        project = self.actions[0].src_project
        other_project = other.actions[0].src_project
        return self.reqid == other.reqid and project == other_project

    def __hash__(self):
        hash_parts = [self.reqid]
        if self.src_project:
            hash_parts.append(self.src_project)
        hashes = [hash(part) for part in hash_parts]
        return sum(hashes)

    def __str__(self):
        return "{0}".format(self.reqid)

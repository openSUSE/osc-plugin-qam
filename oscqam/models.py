"""This module contains all models that are required by the QAM plugin to keep
everything in a consistent state.

"""
import abc
from dateutil import parser
import logging
import re
from xml.etree import cElementTree as ET
import osc.core
import osc.oscerr

from .errors import (NoQamReviewsError,
                     NonMatchingUserGroupsError,
                     MissingSourceProjectError,
                     TestPlanReviewerNotSetError,
                     TestResultMismatchError,
                     TemplateNotFoundError)
from .parsers import TemplateParser
from .utils import https
from .compat import PY3

if PY3:
    from urllib.parse import urlencode
else:
    from urllib import urlencode



class XmlFactoryMixin(object):
    """Can generate an object from xml by recursively parsing the structure.

    It will set properties to the text-property of a node if there are no
    children.

    Otherwise it will parse the children into another node and set the property
    to a list of these new parsed nodes.
    """
    def __init__(self, remote, attributes, children):
        """Will set every element in kwargs to a property of the class.
        """
        attributes.update(children)
        for kwarg in attributes:
            setattr(self, kwarg, attributes[kwarg])

    @staticmethod
    def listify(dictionary, key):
        """Will wrap an existing dictionary key in a list.
        """
        if not isinstance(dictionary[key], list):
            value = dictionary[key]
            del dictionary[key]
            dictionary[key] = [value]

    @classmethod
    def parse_et(cls, remote, et, tag, wrapper_cls = None):
        """Recursively parses an element-tree instance.

        Will iterate over the tag as root-level.
        """
        if not wrapper_cls:
            wrapper_cls = cls
        objects = []
        for request in et.iter(tag):
            attribs = {}
            for attribute in request.attrib:
                attribs[attribute] = request.attrib[attribute]
            kwargs = {}
            for child in request:
                key = child.tag
                subchildren = list(child)
                if subchildren or child.attrib:
                    # Prevent that all children have the same class as the
                    # parent.  This might lead to providing methods that make
                    # no sense.
                    value = cls.parse_et(remote, child, key, XmlFactoryMixin)
                    if len(value) == 1:
                        value = value[0]
                else:
                    if child.text:
                        value = child.text.strip()
                    else:
                        value = None
                if key in kwargs:
                    XmlFactoryMixin.listify(kwargs, key)
                    kwargs[key].append(value)
                else:
                    kwargs[key] = value
            if request.text:
                kwargs['text'] = request.text
            kwargs.update(attribs)
            objects.append(wrapper_cls(remote, attribs, kwargs))
        return objects

    @classmethod
    def parse(cls, remote, xml, tag):
        root = ET.fromstring(xml)
        return cls.parse_et(remote, root, tag, cls)


class Attribute(XmlFactoryMixin):
    reject_reason = "MAINT:RejectReason"

    def __init__(self, remote, attributes, children):
        super(Attribute, self).__init__(remote, attributes, children)
        # We expect the value to be a sequence type even if there is only
        # one reasons specified.
        if not isinstance(self.value, (list, tuple)):
            self.value = [self.value]

    @classmethod
    def parse(cls, remote, xml):
        return super(Attribute, cls).parse(remote, xml, 'attribute')

    @classmethod
    def preset(cls, remote, preset, *value):
        """Create a new attribute from a default attribute.

        Default attributes are stored as class-variables on this class.
        """
        namespace, name = preset.split(":")
        return Attribute(remote,
                         {'namespace': namespace, 'name': name},
                         {'value': value})

    def __eq__(self, other):
        if not isinstance(other, Attribute):
            return False
        return (self.namespace == other.namespace and
                self.name == other.name and
                self.value == other.value)

    def xml(self):
        """Turn this attribute into XML."""
        root = ET.Element('attribute')
        root.set('name', self.name)
        root.set('namespace', self.namespace)
        for val in self.value:
            value = ET.SubElement(root, 'value')
            value.text = val
        return ET.tostring(root)


class Reviewer(object):
    """Superclass for possible reviewer-classes.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def is_qam_group(self):
        """
        :returns: True if the group denotes reviews it's associated with to
            be reviewed by a QAM member.

        """
        pass


class GroupFilter(object):
    """Methods that allow filtering on groups."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def is_qam_group(self):
        pass

    @classmethod
    def for_remote(cls, remote):
        """Return the correct Filter for the given remote."""
        if 'opensuse' in remote.remote:
            return OBSGroupFilter()
        else:
            return IBSGroupFilter()


class OBSGroupFilter(GroupFilter):
    """Methods that allow filtering on groups from OBS."""
    def is_qam_group(self, group):
        return group.name.startswith('qa-opensuse.org')


class IBSGroupFilter(GroupFilter):
    IGNORED_GROUPS = ['qam-auto', 'qam-openqa']

    """Methods that allow filtering on groups from IBS."""
    def is_qam_group(self, group):
        return (group.name.startswith('qam') and
                group.name not in self.IGNORED_GROUPS)


class Group(XmlFactoryMixin, Reviewer):
    """A group object from the build service.
    """

    def __init__(self, remote, attributes, children):
        super(Group, self).__init__(remote, attributes, children)
        self.remote = remote
        self.filter = GroupFilter.for_remote(remote)
        if 'title' in children:
            # We set name to title to ensure equality.  This allows us to
            # prevent having to query *all* groups we need via this method,
            # which could use very many requests.
            self.name = children['title']

    @classmethod
    def parse(cls, remote, xml):
        return super(Group, cls).parse(remote, xml, 'group')

    @classmethod
    def parse_entry(cls, remote, xml):
        return super(Group, cls).parse(remote, xml, 'entry')

    def is_qam_group(self):
        # 'qam-auto' is already used to designate automated reviews:
        # https://gitlab.suse.de/l3ms/osc-plugins (osc-checker-qa.py).
        # It is excluded here, as it does not require manual review
        # by a QAM member.
        return self.filter.is_qam_group(self)

    def __hash__(self):
        # We don't want to hash to the same as only the string.
        return hash(self.name) + hash(type(self))

    def __eq__(self, other):
        if not isinstance(other, Group):
            return False
        return self.name == other.name

    def __str__(self):
        if PY3:
            return self.__unicode__()
        else:
            return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u"{0}".format(self.name)


class User(XmlFactoryMixin, Reviewer):
    """Wraps a user of the obs in an object.

    """
    def __init__(self, remote, attributes, children):
        super(User, self).__init__(remote, attributes, children)
        self.remote = remote
        self._groups = None

    @property
    def groups(self):
        """Read-only property for groups a user is part of.
        """
        # Maybe use a invalidating cache as a trade-off between current
        # information and slow response.
        if not self._groups:
            self._groups = self.remote.groups.for_user(self)
        return self._groups

    @property
    def qam_groups(self):
        """Return only the groups that are part of the qam-workflow."""
        return [group for group in self.groups
                if group.is_qam_group()]

    def reviewable_groups(self, request):
        """Return groups the user could review for the given request.

        :param request: Request to check for open groups.
        :type request: :class:`oscqam.models.Request`

        :returns: set(:class:`oscqam.models.Group`)
        """
        user_groups = set(self.qam_groups)
        reviews = [review for review in request.review_list() if
                   (isinstance(review, GroupReview) and review.open
                    and review.reviewer.is_qam_group())]
        if not reviews:
            raise NoQamReviewsError(reviews)
        review_groups = [review.reviewer for review in reviews]
        open_groups = set(review_groups)
        both = user_groups.intersection(open_groups)
        if not both:
            raise NonMatchingUserGroupsError(self,
                                             user_groups,
                                             open_groups)
        return both

    def in_review_groups(self, request):
        reviewing_groups = []
        for role in request.assigned_roles:
            if role.user == self:
                reviewing_groups.append(role.group)
        return reviewing_groups

    def is_qam_group(self):
        return False

    def __hash__(self):
        return hash(self.login)

    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        return isinstance(other, User) and self.login == other.login

    def __str__(self):
        if PY3:
            return self.__unicode__()
        else:
            return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u"{0} ({1})".format(self.realname, self.email)

    @classmethod
    def parse(cls, remote, xml):
        return super(User, cls).parse(remote, xml, remote.users.endpoint)


class Review(object):
    """Base class for buildservice-review objects.

    """
    OPEN_STATES = ('new', 'review')
    CLOSED_STATES = ('accepted',)

    def __init__(self, remote, review, reviewer):
        self._review = review
        self.remote = remote
        self.reviewer = reviewer
        self.state = review.state.lower()
        self.open = self.state in self.OPEN_STATES
        self.closed = self.state in self.CLOSED_STATES

    def __str__(self):
        if PY3:
            return self.__unicode__()
        else:
            return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u'Review: {0} ({1})'.format(self.reviewer, self.state)


class GroupReview(Review):
    def __init__(self, remote, review):
        reviewer = remote.groups.for_name(review.by_group)
        super(GroupReview, self).__init__(remote, review, reviewer)


class UserReview(Review):
    def __init__(self, remote, review):
        reviewer = remote.users.by_name(review.by_user)
        super(UserReview, self).__init__(remote, review, reviewer)


class Assignment(object):
    """Associates a user with a group in the relation
    '<user> performs review for <group>'.

    This is solely a QAM construct as the buildservice has no concept of these
    assignments.

    """
    ASSIGNED_DESC = "Review got assigned"
    ACCEPTED_DESC = "Review got accepted"
    REOPENED_DESC = "Review got reopened"

    def __init__(self, user, group):
        self.user = user
        self.group = group

    def __hash__(self):
        return hash(self.user) + hash(self.group)

    def __eq__(self, other):
        return (self.user == other.user and
                self.group == other.group)

    def __repr__(self):
        return str(self)

    def __str__(self):
        if PY3:
            return self.__unicode__()
        else:
            return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u"{1} -> {0}".format(self.user, self.group)

    @classmethod
    def infer_group(cls, remote, request, group_review):
        def get_history(review_state):
            """Return the history events for the given state that are needed to
            find assignments in ascending order of occurrence (by date).

            """
            events = review_state.statehistory
            relevant_events = filter(
                lambda e: e.get_description() in [cls.ASSIGNED_DESC,
                                                  cls.ACCEPTED_DESC,
                                                  cls.REOPENED_DESC],
                events
            )
            return sorted(relevant_events,
                          key=lambda e: parser.parse(e.when))
        group = group_review.reviewer
        review_state = [r for r in request.reviews
                        if r.by_group == group.name][0]
        events = get_history(review_state)
        assignments = set()
        for event in events:
            user = remote.users.by_name(event.who)
            if event.get_description() == cls.ACCEPTED_DESC:
                logging.debug("Assignment for: {g} -> {u}".format(g=group,
                                                                  u=user))
                assignments.add(Assignment(user, group))
            elif event.get_description() == cls.REOPENED_DESC:
                logging.debug("Unassignment for: {g} -> {u}".format(g=group,
                                                                    u=user))
                assignments.remove(Assignment(user, group))
            else:
                logging.debug("Unknown event: {e}".format(
                    e=event.get_description())
                )
        return assignments

    @classmethod
    def infer(cls, remote, request):
        """Create assignments for the given request.

        First assignments will be found for all groups that are of interest.

        Once the group assignments (to users) are found, the already finished
        ones will be removed.

        :param request: Request to check for a possible assigned roles.
        :type request: :class:`oscqam.models.Request`

        :returns: [:class:`oscqam.models.Assignment`]

        """
        assigned_groups = [g for g in request.review_list()
                           if isinstance(g, GroupReview) and g.state == 'accepted'
                           and g.reviewer.is_qam_group()]
        unassigned_groups = [g for g in request.review_list()
                             if isinstance(g, GroupReview) and g.state == 'new'
                             and g.reviewer.is_qam_group()]
        finished_user = [u for u in request.review_list()
                         if isinstance(u, UserReview) and u.state == 'accepted']
        assignments = set()
        for group_review in set(assigned_groups) | set(unassigned_groups):
            assignments.update(cls.infer_group(remote, request, group_review))
        for user_review in finished_user:
            removal = [a for a in assignments if a.user == user_review.reviewer]
            if removal:
                logging.debug(
                    "Removing assignments {r} as they are finished".format(
                        r=removal
                    ))
                for r in removal:
                    assignments.remove(r)
        if not assignments:
            logging.debug(
                "No assignments could be found for {0}".format(request)
            )
        return list(assignments)


class RequestFilter(object):
    """Methods that allow filtering on requests."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def maintenance_requests(self, requests):
        pass

    @classmethod
    def for_remote(cls, remote):
        """Return the correct Filter for the given remote."""
        if 'opensuse' in remote.remote:
            return OBSRequestFilter()
        else:
            return IBSRequestFilter()


class OBSRequestFilter(RequestFilter):
    PREFIX = "openSUSE:Maintenance"

    def maintenance_requests(self, requests):
        return [r for r in requests if self.PREFIX in r.src_project]


class IBSRequestFilter(RequestFilter):
    PREFIX = "SUSE:Maintenance"

    def maintenance_requests(self, requests):
        return [r for r in requests if self.PREFIX in r.src_project]


class Request(osc.core.Request, XmlFactoryMixin):
    """Wrapper around osc request object to add logic required by the
    qam-plugin.
    """
    STATE_NEW = 'new'
    STATE_REVIEW = 'review'
    STATE_DECLINED = 'declined'
    OPEN_STATES = [STATE_NEW, STATE_REVIEW]
    REVIEW_USER = 'BY_USER'
    REVIEW_GROUP = 'BY_GROUP'
    REVIEW_OTHER = 'BY_OTHER'
    COMPLETE_REQUEST_ID_SRE = re.compile(
        r"(open)?SUSE:Maintenance:\d+:(?P<req>\d+)"
    )

    def __init__(self, remote):
        self.remote = remote
        super(Request, self).__init__()
        self._comments = None
        self._groups = None
        self._packages = None
        self._assigned_roles = None
        self._priority = None
        self._reviews = []
        self._attributes = {}
        self._issues = []

    def active(self):
        return self.state == 'new' or self.state == 'review'

    @property
    def incident_priority(self):
        if not self._priority:
            self._priority = self.remote.priorities.for_request(self)
        return self._priority

    @property
    def assigned_roles(self):
        if not self._assigned_roles:
            self._assigned_roles = Assignment.infer(self.remote, self)
        return self._assigned_roles

    @property
    def comments(self):
        if not self._comments:
            self._comments = (self.remote.comments.for_request(self) or
                              [Comment.none])
        return self._comments

    @property
    def maker(self):
        for history in self.statehistory:
            if history.description == "Request created":
                self._creator = self.remote.users.by_name(history.who)
                break
        else:
            self._creator = "Unknown"
        return self._creator

    @property
    def issues(self):
        """Bugs that should be fixed as part of this request"""
        if not self._issues:
            self._issues = self.remote.bugs.for_request(self)
        return self._issues

    @property
    def groups(self):
        # Maybe use a invalidating cache as a trade-off between current
        # information and slow response.
        return [review.reviewer for review in self.review_list()
                if isinstance(review, GroupReview)]

    @property
    def packages(self):
        """Collects all packages of the actions that are part of the request.
        """
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

        """
        for action in self.actions:
            if hasattr(action, 'src_project'):
                prj = action.src_project
                if prj:
                    return prj
                else:
                    logging.info("This project has no source project: %s", self.reqid)
                    return ''
        return ''

    def attribute(self, attribute):
        """Load the specified attribute for this request.

        As requests right now can not contain attributes the attribute will be
        loaded from the corresponding source-project.
        """
        if attribute not in self._attributes:
            attributes = self.remote.projects.get_attribute(
                self.src_project, attribute
            )
            if len(attributes) == 1:
                attributes = attributes[0]
            self._attributes[attribute] = attributes
        return self._attributes[attribute]

    def review_action(self, params, user = None, group = None, comment = None):
        if not user and not group:
            raise AttributeError("group or user required for this action.")
        if user:
            params['by_user'] = user.login
        if group:
            params['by_group'] = group.name
        url_params = urlencode(params)
        url = "/".join([self.remote.requests.endpoint, self.reqid])
        url += "?" + url_params
        self.remote.post(url, comment)

    def review_assign(self, group, reviewer, comment = None):
        params = {'cmd': 'assignreview',
                  'reviewer': reviewer.login}
        self.review_action(params, group = group, comment = comment)

    def review_accept(self, user = None, group = None, comment = None):
        comment = self._format_review_comment(comment)
        params = {'cmd': 'changereviewstate',
                  'newstate': 'accepted'}
        self.review_action(params, user, group, comment)

    def review_add(self, user = None, group = None, comment = None):
        """Will add a new reviewrequest for the given user or group.

        """
        comment = self._format_review_comment(comment)
        params = {'cmd': 'addreview'}
        self.review_action(params, user, group, comment)

    def review_decline(self, user = None, group = None, comment = None,
                       reasons = None):
        """Will decline the reviewrequest for the given user or group.

        :param user: The user declining the request.

        :param group: The group the request should be declined for.

        :param comment: A comment that will be added to describe why the
            request was declined.

        :param reason: A L{oscqam.reject_reasons.RejectReason} that
            explains why the request was declined.
            The reason will be added as an attribute to the Maintenance
            incident.
        """
        if reasons:
            reason = self._build_reject_attribute(reasons)
            self.remote.projects.set_attribute(self.src_project, reason)
        comment = self._format_review_comment(comment)
        params = {'cmd': 'changereviewstate',
                  'newstate': 'declined'}
        self.review_action(params, user, group, comment)

    def _build_reject_attribute(self, reasons):
        reject_reason = self.attribute(Attribute.reject_reason)
        reason_values = list(map(lambda reason: "{0}:{1}".format(self.reqid,
                                                            reason.flag),
                            reasons))
        if not reject_reason:
            reject_reason = Attribute.preset(self.remote,
                                             Attribute.reject_reason,
                                             *reason_values)
        else:
            for r in reason_values:
                reject_reason.value.append(r)
        return reject_reason

    def review_reopen(self, user = None, group = None, comment = None):
        """Will reopen a reviewrequest for the given user or group.

        """
        params = {'cmd': 'changereviewstate',
                  'newstate': 'new'}
        self.review_action(params, user, group, comment)

    def _format_review_comment(self, comment):
        if not comment:
            return None
        return "[oscqam] {comment}".format(comment = comment)

    def review_list(self):
        """Returns all reviews as a list.
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
        """
        return [r for r in self.review_list() if r.state in
                Request.OPEN_STATES]

    def review_list_accepted(self):
        return [r for r in self.review_list()
                if r.state.lower() == 'accepted']

    def add_comment(self, comment):
        """Adds a comment to this request.
        """
        endpoint = '/comments/request/{id}'.format(id = self.reqid)
        self.remote.post(endpoint, comment)

    def get_template(self, template_factory):
        """Return the template associated with this request.
        """
        if not self.src_project:
            raise MissingSourceProjectError(self)
        return template_factory(self)

    @classmethod
    def filter_by_project(cls, request_substring, requests):
        requests = [r for r in requests if request_substring in r.src_project]
        return requests

    @classmethod
    def parse(cls, remote, xml):
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
                if not (osc.core.get_osc_version() < '0.152'):
                    raise
                if 'acceptinfo' not in str(e):
                    raise
                else:
                    logging.error(
                        "Server version too high for osc-client: %s" % str(e)
                    )
                    pass
        return requests

    @classmethod
    def parse_request_id(cls, request_id):
        """Extract the request_id from a string if required.

        The method will extract the request-id of a complete request string
        (e.g. SUSE:Maintenance:123:45678 has a request id of 45678) if
        needed.

        """
        reqid = cls.COMPLETE_REQUEST_ID_SRE.match(request_id)
        if reqid:
            return reqid.group('req')
        return request_id

    def __eq__(self, other):
        project = self.actions[0].src_project
        other_project = other.actions[0].src_project
        return (self.reqid == other.reqid and
                project == other_project)

    def __hash__(self):
        hash_parts = [self.reqid]
        if self.src_project:
            hash_parts.append(self.src_project)
        hashes = [hash(part) for part in hash_parts]
        return sum(hashes)

    def __str__(self):
        if PY3:
            return self.__unicode__()
        else:
            return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u"{0}".format(self.reqid)


class NullComment(object):
    """Null-Object for comments.
    """
    def __init__(self):
        self.id = None
        self.text = None

    def __str__(self):
        if PY3:
            return self.__unicode__()
        else:
            return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u""


class Comment(XmlFactoryMixin):
    none = NullComment()

    def delete(self):
        self.remote.comments.delete(self)

    @classmethod
    def parse(cls, remote, xml):
        return super(Comment, cls).parse(remote, xml, 'comment')

    def __str__(self):
        if PY3:
            return self.__unicode__()
        else:
            return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u"{0}: {1}".format(self.id, self.text)


class Template(object):
    """Facade to web-based templates.
    The templates can be found in:

    ``https://qam.suse.de/testreports/``
    """
    STATUS_SUCCESS = 0
    STATUS_FAILURE = 1
    STATUS_UNKNOWN = 2
    base_url = "https://qam.suse.de/testreports/"

    def get_testreport_web(log_path):
        """Load the template belonging to the request from
        https://qam.suse.de/testreports/.

        :param request: The request this template is associated with.
        :type request: :class:`oscqam.models.Request`

        :return: Content of the log-file as string.

        """
        report = https(log_path)
        if not report:
            raise TemplateNotFoundError(log_path)
        return report.read()

    def __init__(self, request, tr_getter = get_testreport_web,
                 parser = TemplateParser()):
        """Create a template from the given request.

        :param request: The request the template is associated with.
        :type request: :class:`oscqam.models.Request`.

        :param tr_getter: Function that can load the template's log file based
                          on the request. Will default to loading testreports
                          from http://qam.suse.de.

        :type tr_getter: Function: :class:`oscqam.models.Request` ->
                         :class:`str`

        :param parser: Class that can parse the data returned by tr_getter.
        :type parser: :class:`oscqam.parsers.TemplateParser`

        """
        self._request = request
        self._log_path = self.url()
        self.log_entries = parser(tr_getter(self._log_path))

    def failed(self):
        """Assert that this template is from a failed test.

        If the template says the test did not fail this will raise an error.

        """
        if self.status != Template.STATUS_FAILURE:
            raise TestResultMismatchError(
                'FAILED',
                self._log_path
            )

    def passed(self):
        """Assert that this template is from a successful test.

        :raises: :class:`oscqam.models.TestResultMismatchError` if template is
            not set to PASSED.
        """
        if self.status != Template.STATUS_SUCCESS:
            raise TestResultMismatchError(
                'PASSED',
                self._log_path
            )

    def testplanreviewer(self):
        """Assert that the Test Plan Reviewer for the template is set.

        :raises: :class:`oscqam.models.TestPlanReviewerNotSetError` if reviewer
            is not set or empty.
        """
        reviewer = self.log_entries.get('Test Plan Reviewer', '')
        reviewer = self.log_entries.get('Test Plan Reviewers', reviewer)
        reviewer = reviewer.strip()
        if reviewer:
            return reviewer
        raise TestPlanReviewerNotSetError(self._log_path)

    @property
    def status(self):
        summary = self.log_entries['SUMMARY']
        if summary.upper() == "PASSED":
            return Template.STATUS_SUCCESS
        elif summary.upper() == "FAILED":
            return Template.STATUS_FAILURE
        return Template.STATUS_UNKNOWN

    def url(self):
        return "{base}{prj}:{reqid}/log".format(
            base = self.base_url,
            prj = self._request.src_project,
            reqid = self._request.reqid
        )


class Bug(XmlFactoryMixin):
    def __str__(self):
        if PY3:
            return self.__unicode__()
        else:
            return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u"{0}:{1}".format(self.tracker, self.id)


def monkeypatch():
    """Monkey patch retaining of history into the review class.
    """
    def monkey_patched_init(obj, review_node):
        # logging.debug("Monkeypatched init")
        original_init(obj, review_node)
        obj.statehistory = []
        for hist_state in review_node.findall('history'):
            obj.statehistory.append(osc.core.RequestHistory(hist_state))
    # logging.warn("Careful - your osc-version requires monkey patching.")
    original_init = osc.core.ReviewState.__init__
    osc.core.ReviewState.__init__ = monkey_patched_init


monkeypatch()

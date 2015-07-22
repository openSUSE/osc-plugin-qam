"""This module contains all models that are required by the QAM plugin to keep
everything in a consistent state.

"""
import abc
import contextlib
import logging
import re
import urllib
import urllib2
try:
    from xml.etree import cElementTree as ET
except ImportError:
    import cElementTree as ET
import osc.core
import osc.oscerr

from .compat import total_ordering
from .parsers import TemplateParser

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def et_iter(elementtree, tag):
    """This function is used to make the iter call work in
    version < 2.7 as well.
    """
    if hasattr(elementtree, 'iter'):
        return elementtree.iter(tag)
    else:
        return elementtree.getiterator(tag)


class ReportedError(RuntimeError):
    """Raise on exceptions that can only be reported but not handled."""


class InvalidRequestError(ReportedError):
    """Raise when a request object is missing required information."""
    def __init__(self, request):
        super(InvalidRequestError, self).__init__(
            "Invalid build service request: {0}".format(request)
        )


class MissingSourceProjectError(InvalidRequestError):
    """Raise when a request is missing the source project property."""
    def __init__(self, request):
        super(MissingSourceProjectError, self).__init__(
            "Invalid build service request: "
            "{0} has no source project.".format(request)
        )


class TemplateNotFoundError(ReportedError):
    """Raise when a template could not be found."""
    def __init__(self, message):
        super(TemplateNotFoundError, self).__init__(
            "Report could not be loaded: {0}".format(message)
        )


class TestResultMismatchError(ReportedError):
    _msg = "Request-Status not '{0}': please check report: {1}"

    def __init__(self, expected, log_path):
        super(TestResultMismatchError, self).__init__(
            self._msg.format(expected, log_path)
        )


class TestPlanReviewerNotSetError(ReportedError):
    _msg = ("The testreport ({path}) is missing a test plan reviewer.")

    def __init__(self, path):
        super(TestPlanReviewerNotSetError, self).__init__(
            self._msg.format(path = path)
        )


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
        for request in et_iter(et, tag):
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


class Group(XmlFactoryMixin, Reviewer):
    """A group object from the build service.
    """

    def __init__(self, remote, attributes, children):
        super(Group, self).__init__(remote, attributes, children)
        self.remote = remote
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
        return self.name.startswith('qam') and self.name != 'qam-auto'

    def __hash__(self):
        # We don't want to hash to the same as only the string.
        return hash(self.name) + hash(type(self))

    def __eq__(self, other):
        if not isinstance(other, Group):
            return False
        return self.name == other.name

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u"{0}".format(self.name)


class User(XmlFactoryMixin, Reviewer):
    """Wraps a user of the obs in an object.

    """
    QAM_SRE = re.compile(".*qam.*")

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
                if User.QAM_SRE.match(group.name)]

    def is_qam_group(self):
        return False

    def __hash__(self):
        return hash(self.login)

    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        return isinstance(other, User) and self.login == other.login

    def __str__(self):
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
    def __init__(self, user, group):
        self.user = user
        self.group = group

    def __hash__(self):
        return hash(self.user) + hash(self.group)

    def __eq__(self, other):
        return (self.user == other.user and
                self.group == other.group)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u"{1} -> {0}".format(self.user, self.group)

    @staticmethod
    def infer_by_single_group(request):
        """Return an :class:`oscqam.models.Assignment` for the request if
        only one group is assigned for review.

        This will be interpreted as the only possible group that can be
        reviewed by an open user-review.

        :param request: Request to check for a possible assigned role.
        :type request: :class:`oscqam.models.Request`

        :returns: set(:class:`oscqam.models.Assignment`)

        """
        accepted = [r for r in request.review_list_accepted()
                    if r.reviewer.is_qam_group()]
        if not len(accepted) == 1:
            return set()
        users = [r for r in request.review_list_open()
                 if isinstance(r, UserReview)]
        if not len(users) == 1:
            logger.debug(
                "No user for an assigned group-review:"
                "Group: {0}, Request {1}.".format(accepted[0].reviewer,
                                                  request)
            )
            return set()
        group = accepted[0].reviewer
        user = users[0].reviewer
        return set([Assignment(user, group)])

    @staticmethod
    def infer_by_comments(request):
        """Return assignments for the request based on comments.

        :param request: Request to check for a possible assigned roles.
        :type request: :class:`oscqam.models.Request`

        :returns: [:class:`oscqam.models.Assignment`]
        """
        def is_assignment(event):
            return "Review got assigned" in event.description

        def is_unassignment(event):
            return ("Review got reopened" in event.description and
                    "unassign" in event.comment)

        def is_accepted(event):
            return ("Review got accepted in event.description" and
                    (not event.comment or
                    "[qamosc]::accept" in event.comment))
        assignments = []
        closed_group_reviews = [review for review in request.review_list()
                                if isinstance(review, GroupReview) and
                                review.closed]
        closed_groups = set([review.reviewer for review in
                             closed_group_reviews])
        open_user_reviews = [review for review in request.review_list()
                             if isinstance(review, UserReview) and
                             review.open]
        open_users = set([review.reviewer for review in open_user_reviews])
        assignment_user_regex = re.compile(
            "review assigend to user (?P<user>.+)"
        )
        assignment_group_regex = re.compile("review for group (?P<group>.+)")
        previous_event = None
        for event in request.statehistory:
            logger.debug("Event: {event.comment}".format(event = event))
            group_match = assignment_group_regex.match(event.comment)
            if group_match:
                group = request.remote.groups.for_name(
                    group_match.group('group')
                )
                if group in closed_groups:
                    user_match = assignment_user_regex.match(
                        previous_event.comment
                    )
                    if user_match:
                        user = request.remote.users.by_name(
                            user_match.group('user')
                        )
                        if user in open_users:
                            assignments.append(Assignment(user, group))
            previous_event = event
        return assignments

    @classmethod
    def infer(cls, request):
        """Create assignments for the given request.

        This code uses heuristics to find assignments as the build service
        does not have the concept of a review being done by a user:
        a relation 'group review is performed by user' is inferred from
        the request via the following two approaches:

        1. If only one group-review and one user-review exist, it is
        assumed that the user is performing the review for the group.

        2. If multiple group-reviews exist the user-reviews must be inferred
        via comments - this uses the fact that the new 'addreview' command
        always adds a comment of the form 'review for group <group>'.
        However if a user chooses to accept the review by hand and add a new
        review for himself, this will not happen (e.g. by using
        ``osc review command``).

        :param request: Request to check for a possible assigned roles.
        :type request: :class:`oscqam.models.Request`

        :returns: [:class:`oscqam.models.Assignment`]

        """
        assignments = set()
        assignments.update(cls.infer_by_single_group(request))
        assignments.update(cls.infer_by_comments(request))
        if not assignments:
            logger.debug(
                "No assignments could be found for {0}".format(request)
            )
        return list(assignments)


class Request(osc.core.Request, XmlFactoryMixin):
    """Wrapper around osc request object to add logic required by the
    qam-plugin.
    """
    @total_ordering
    class Priority(object):
        """Store the priority of this request's associated incident.
        """
        def __init__(self, prio):
            self.priority = int(prio)

        def __eq__(self, other):
            return self.priority == other.priority

        def __lt__(self, other):
            return (self.priority > other.priority)

        def __str__(self):
            return "{0}".format(self.priority)

    class UnknownPriority(Priority):
        def __init__(self):
            self.priority = None

        def __eq__(self, other):
            return isinstance(other, Request.UnknownPriority)

        def __lt__(self, other):
            return False

        def __str__(self):
            return unicode(self).encode('utf-8')

        def __unicode__(self):
            return u"{0}".format(self.priority)

    OPEN_STATES = ['new', 'review']
    REVIEW_USER = 'BY_USER'
    REVIEW_GROUP = 'BY_GROUP'
    REVIEW_OTHER = 'BY_OTHER'
    COMPLETE_REQUEST_ID_SRE = re.compile("SUSE:Maintenance:\d+:(?P<req>\d+)")

    def __init__(self, remote):
        self.remote = remote
        super(Request, self).__init__()
        self._groups = None
        self._packages = None
        self._assigned_roles = None
        self._priority = None
        self._reviews = []

    @property
    def incident_priority(self):
        if not self._priority:
            endpoint = "/source/{0}/_attribute/OBS:IncidentPriority".format(
                self.src_project
            )
            try:
                xml = ET.fromstring(self.remote.get(endpoint))
            except urllib2.HTTPError:
                logger.error("Priority not found: %s", endpoint)
                self._priority = self.UnknownPriority()
            else:
                value = xml.find(".//value")
                try:
                    self._priority = self.Priority(value.text)
                except AttributeError:
                    self._priority = self.UnknownPriority()
        return self._priority

    @property
    def assigned_roles(self):
        if not self._assigned_roles:
            self._assigned_roles = Assignment.infer(self)
        return self._assigned_roles

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
                    logger.info("This project has no source project: %s",
                                self.reqid)
                    return ''
        return ''

    def review_action(self, params, user = None, group = None, comment = None):
        if not user and not group:
            raise AttributeError("group or user required for this action.")
        if user:
            params['by_user'] = user.login
        if group:
            params['by_group'] = group.name
        url_params = urllib.urlencode(params)
        url = "/".join([self.remote.requests.endpoint, self.reqid])
        url += "?" + url_params
        self.remote.post(url, comment)

    def review_assign(self, group, reviewer, comment = None):
        params = {'cmd': 'assignreview',
                  'reviewer': reviewer.login}
        self.review_action(params, group = group, comment = comment)

    def review_accept(self, user = None, group = None, comment = None):
        comment = "[qamosc]::accept::{user}::{group}".format(
            user = user, group = group
        )
        params = {'cmd': 'changereviewstate',
                  'newstate': 'accepted'}
        self.review_action(params, user, group, comment)

    def review_add(self, user = None, group = None, comment = None):
        """Will add a new reviewrequest for the given user or group.

        """
        params = {'cmd': 'addreview'}
        self.review_action(params, user, group, comment)

    def review_decline(self, user = None, group = None, comment = None):
        """Will decline the reviewrequest for the given user or group.

        """
        params = {'cmd': 'changereviewstate',
                  'newstate': 'declined'}
        self.review_action(params, user, group, comment)

    def review_reopen(self, user = None, group = None, comment = None):
        """Will reopen a reviewrequest for the given user or group.

        """
        params = {'cmd': 'changereviewstate',
                  'newstate': 'new'}
        self.review_action(params, user, group, comment)

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
        for request in et_iter(et, remote.requests.endpoint):
            try:
                req = Request(remote)
                req.read(request)
                requests.append(req)
            except osc.oscerr.APIError as e:
                logger.error(e.msg)
                pass
            except osc.oscerr.WrongArgs as e:
                # Temporary workaround, as OBS >= 2.7 can return requests with
                # acceptinfo-elements that old osc can not handle.
                if not (osc.core.get_osc_version() < '0.152'):
                    raise
                if not 'acceptinfo' in str(e):
                    raise
                else:
                    logger.error(
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
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u"{0}".format(self.reqid)


class Template(object):
    """Facade to web-based templates.
    The templates can be found in:

    ``http://qam.suse.de/testreports/``
    """
    STATUS_SUCCESS = 0
    STATUS_FAILURE = 1
    STATUS_UNKNOWN = 2
    base_url = "http://qam.suse.de/testreports/"

    def get_testreport_web(log_path):
        """Load the template belonging to the request from
        http://qam.suse.de/testreports/.

        :param request: The request this template is associated with.
        :type request: :class:`oscqam.models.Request`

        :return: Content of the log-file as string.

        """
        try:
            with contextlib.closing(urllib2.urlopen(log_path)) as log_file:
                return log_file.read()
        except urllib2.URLError:
            raise TemplateNotFoundError(log_path)

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
        self._log_path = "{base}{prj}:{reqid}/log".format(
            base = self.base_url,
            prj = request.src_project,
            reqid = request.reqid
        )
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


def monkeypatch():
    """Monkey patch retaining of history into the review class.
    """
    def monkey_patched_init(obj, review_node):
        # logger.debug("Monkeypatched init")
        original_init(obj, review_node)
        obj.statehistory = []
        for hist_state in review_node.findall('history'):
            obj.statehistory.append(osc.core.RequestHistory(hist_state))
    # logger.warn("Careful - your osc-version requires monkey patching.")
    original_init = osc.core.ReviewState.__init__
    osc.core.ReviewState.__init__ = monkey_patched_init

monkeypatch()

"""Provides a class for representing users."""

from ..errors import NoQamReviewsError, NonMatchingUserGroupsError
from .review import GroupReview
from .reviewer import Reviewer
from .xmlfactorymixin import XmlFactoryMixin


class User(XmlFactoryMixin, Reviewer):
    """Wraps a user of the obs in an object.

    Attributes:
        remote: A remote facade.
        login: The user's login name.
        realname: The user's real name.
        email: The user's email address.
    """

    def __init__(self, remote, attributes, children):
        """Initializes a User.

        Args:
            remote: A remote facade.
            attributes: A dictionary of attributes for the XML element.
            children: A dictionary of child elements for the XML element.
        """
        super().__init__(remote, attributes, children)
        self.remote = remote
        self._groups = None

    @property
    def groups(self):
        """Read-only property for groups a user is part of.

        Returns:
            A list of Group objects.
        """
        # Maybe use a invalidating cache as a trade-off between current
        # information and slow response.
        if not self._groups:
            self._groups = self.remote.groups.for_user(self)
        return self._groups

    @property
    def qam_groups(self):
        """Return only the groups that are part of the qam-workflow.

        Returns:
            A list of QAM Group objects.
        """
        return [group for group in self.groups if group.is_qam_group()]

    def reviewable_groups(self, request):
        """Return groups the user could review for the given request.

        Args:
            request: Request to check for open groups.

        Returns:
            A set of Group objects the user can review for.

        Raises:
            NoQamReviewsError: If there are no open QAM reviews for the request.
            NonMatchingUserGroupsError: If the user is not in any of the groups
                that can review the request.
        """
        user_groups = set(self.qam_groups)
        reviews = [
            review
            for review in request.review_list()
            if (
                isinstance(review, GroupReview)
                and review.open
                and review.reviewer.is_qam_group()
            )
        ]
        if not reviews:
            raise NoQamReviewsError(reviews)
        review_groups = [review.reviewer for review in reviews]
        open_groups = set(review_groups)
        both = user_groups.intersection(open_groups)
        if not both:
            raise NonMatchingUserGroupsError(self, user_groups, open_groups)
        return both

    def in_review_groups(self, request):
        """Returns the groups the user is currently reviewing for a request.

        Args:
            request: The request to check.

        Returns:
            A list of Group objects.
        """
        reviewing_groups = []
        for role in request.assigned_roles:
            if role.user == self:
                reviewing_groups.append(role.group)
        return reviewing_groups

    def is_qam_group(self):
        """Checks if the user is a QAM group.

        This always returns False for a User object.

        Returns:
            False.
        """
        return False

    def __hash__(self):
        """Returns a hash for the user.

        Returns:
            An integer hash value based on the user's login.
        """
        return hash(self.login)

    def __eq__(self, other):
        """Checks if two users are equal.

        Args:
            other: The other user to compare to.

        Returns:
            True if the users have the same login, False otherwise.
        """
        if not isinstance(other, User):
            return False
        return isinstance(other, User) and self.login == other.login

    def __str__(self):
        """Returns a string representation of the user.

        Returns:
            A string in the format "realname (email)".
        """
        return "{0} ({1})".format(self.realname, self.email)

    @classmethod
    def parse(cls, remote, xml):
        """Parses a user from XML.

        Args:
            remote: A remote facade.
            xml: The XML to parse.

        Returns:
            A User object.
        """
        return super(User, cls).parse(remote, xml, remote.users.endpoint)

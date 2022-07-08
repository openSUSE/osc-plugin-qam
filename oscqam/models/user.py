from ..errors import NoQamReviewsError, NonMatchingUserGroupsError
from .review import GroupReview
from .reviewer import Reviewer
from .xmlfactorymixin import XmlFactoryMixin


class User(XmlFactoryMixin, Reviewer):
    """Wraps a user of the obs in an object."""

    def __init__(self, remote, attributes, children):
        super().__init__(remote, attributes, children)
        self.remote = remote
        self._groups = None

    @property
    def groups(self):
        """Read-only property for groups a user is part of."""
        # Maybe use a invalidating cache as a trade-off between current
        # information and slow response.
        if not self._groups:
            self._groups = self.remote.groups.for_user(self)
        return self._groups

    @property
    def qam_groups(self):
        """Return only the groups that are part of the qam-workflow."""
        return [group for group in self.groups if group.is_qam_group()]

    def reviewable_groups(self, request):
        """Return groups the user could review for the given request.

        :param request: Request to check for open groups.
        :type request: :class:`oscqam.models.Request`

        :returns: set(:class:`oscqam.models.Group`)
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
        return "{0} ({1})".format(self.realname, self.email)

    @classmethod
    def parse(cls, remote, xml):
        return super(User, cls).parse(remote, xml, remote.users.endpoint)

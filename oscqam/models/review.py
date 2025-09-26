"""Provides classes for representing reviews."""


class Review:
    """Base class for buildservice-review objects.

    Attributes:
        OPEN_STATES: A tuple of strings representing open review states.
        CLOSED_STATES: A tuple of strings representing closed review states.
        remote: A remote facade.
        reviewer: The reviewer of the review.
        state: The state of the review.
        open: A boolean indicating if the review is open.
        closed: A boolean indicating if the review is closed.
    """

    OPEN_STATES = ("new", "review")
    CLOSED_STATES = ("accepted",)

    def __init__(self, remote, review, reviewer):
        """Initializes a Review.

        Args:
            remote: A remote facade.
            review: The review object from the build service.
            reviewer: The reviewer of the review.
        """
        self._review = review
        self.remote = remote
        self.reviewer = reviewer
        self.state = review.state.lower()
        self.open = self.state in self.OPEN_STATES
        self.closed = self.state in self.CLOSED_STATES

    def __str__(self):
        """Returns a string representation of the review.

        Returns:
            A string in the format "Review: reviewer (state)".
        """
        return "Review: {0} ({1})".format(self.reviewer, self.state)


class GroupReview(Review):
    """Represents a review by a group."""

    def __init__(self, remote, review):
        """Initializes a GroupReview.

        Args:
            remote: A remote facade.
            review: The review object from the build service.
        """
        reviewer = remote.groups.for_name(review.by_group)
        super().__init__(remote, review, reviewer)


class UserReview(Review):
    """Represents a review by a user."""

    def __init__(self, remote, review):
        """Initializes a UserReview.

        Args:
            remote: A remote facade.
            review: The review object from the build service.
        """
        reviewer = remote.users.by_name(review.by_user)
        super().__init__(remote, review, reviewer)

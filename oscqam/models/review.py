class Review:
    """Base class for buildservice-review objects."""

    OPEN_STATES = ("new", "review")
    CLOSED_STATES = ("accepted",)

    def __init__(self, remote, review, reviewer):
        self._review = review
        self.remote = remote
        self.reviewer = reviewer
        self.state = review.state.lower()
        self.open = self.state in self.OPEN_STATES
        self.closed = self.state in self.CLOSED_STATES

    def __str__(self):
        return "Review: {0} ({1})".format(self.reviewer, self.state)


class GroupReview(Review):
    def __init__(self, remote, review):
        reviewer = remote.groups.for_name(review.by_group)
        super().__init__(remote, review, reviewer)


class UserReview(Review):
    def __init__(self, remote, review):
        reviewer = remote.users.by_name(review.by_user)
        super().__init__(remote, review, reviewer)

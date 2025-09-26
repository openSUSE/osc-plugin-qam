"""Represents the assignment of a user to a group for a review."""

import logging

from dateutil import parser

from .review import GroupReview, UserReview


class Assignment:
    """Associates a user with a group in the relation
    '<user> performs review for <group>'.

    This is solely a QAM construct as the buildservice has no concept of these
    assignments.

    Attributes:
        ASSIGNED_DESC: A string describing an assigned review.
        ACCEPTED_DESC: A string describing an accepted review.
        REOPENED_DESC: A string describing a reopened review.
        user: The user assigned to the review.
        group: The group the user is assigned to review for.
    """

    ASSIGNED_DESC = "Review got assigned"
    ACCEPTED_DESC = "Review got accepted"
    REOPENED_DESC = "Review got reopened"

    def __init__(self, user, group):
        """Initializes an Assignment.

        Args:
            user: The user to assign.
            group: The group to assign the user to.
        """
        self.user = user
        self.group = group

    def __hash__(self):
        return hash(self.user) + hash(self.group)

    def __eq__(self, other):
        return self.user == other.user and self.group == other.group

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "{1} -> {0}".format(self.user, self.group)

    @classmethod
    def infer_group(cls, remote, request, group_review):
        """Infers assignments for a specific group review.

        Args:
            remote: A remote facade.
            request: The request to infer assignments for.
            group_review: The group review to infer assignments from.

        Returns:
            A set of assignments for the group.
        """

        def get_history(review_state):
            """Return the history events for the given state that are needed to
            find assignments in ascending order of occurrence (by date).

            Args:
                review_state: The review state to get history from.

            Returns:
                A sorted list of relevant history events.
            """
            events = review_state.statehistory
            # TODO: refactor out lambda and filter ...
            relevant_events = filter(
                lambda e: e.get_description()
                in [cls.ASSIGNED_DESC, cls.ACCEPTED_DESC, cls.REOPENED_DESC],
                events,
            )
            return sorted(relevant_events, key=lambda e: parser.parse(e.when))

        group = group_review.reviewer
        review_state = [r for r in request.reviews if r.by_group == group.name][0]
        events = get_history(review_state)
        assignments = set()
        for event in events:
            user = remote.users.by_name(event.who)
            if event.get_description() == cls.ACCEPTED_DESC:
                logging.debug("Assignment for: %s -> %s" % (group, user))
                assignments.add(Assignment(user, group))
            elif event.get_description() == cls.REOPENED_DESC:
                logging.debug("Unassignment for: %s -> %s" % (group, user))
                if Assignment(user, group) in assignments:
                    assignments.remove(Assignment(user, group))
            else:
                logging.debug("Unknown event: %s " % event.get_description())
        return assignments

    @classmethod
    def infer(cls, remote, request):
        """Create assignments for the given request.

        First assignments will be found for all groups that are of interest.

        Once the group assignments (to users) are found, the already finished
        ones will be removed.

        Args:
            remote: A remote facade.
            request: Request to check for a possible assigned roles.

        Returns:
            A list of assignments.
        """
        assigned_groups = [
            g
            for g in request.review_list()
            if isinstance(g, GroupReview)
            and g.state == "accepted"
            and g.reviewer.is_qam_group()
        ]
        unassigned_groups = [
            g
            for g in request.review_list()
            if isinstance(g, GroupReview)
            and g.state == "new"
            and g.reviewer.is_qam_group()
        ]
        finished_user = [
            u
            for u in request.review_list()
            if isinstance(u, UserReview) and u.state == "accepted"
        ]
        assignments = set()

        for group_review in set(assigned_groups) | set(unassigned_groups):
            assignments.update(cls.infer_group(remote, request, group_review))

        for user_review in finished_user:
            removal = [a for a in assignments if a.user == user_review.reviewer]

            if removal:
                logging.debug("Removing assignments %s as they are finished" % removal)

                for r in removal:
                    assignments.remove(r)

        if not assignments:
            logging.debug("No assignments could be found for %s" % request)
        return list(assignments)

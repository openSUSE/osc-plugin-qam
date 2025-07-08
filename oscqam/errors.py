from osc.oscerr import OscBaseError


class ReportedError(OscBaseError):
    """Raise on exceptions that can only be reported but not handled."""

    return_code = 10


class UninferableError(ReportedError, ValueError):
    """Error to raise when the program should try to auto-infer some values, but
    can not do so due to ambiguity.

    """


class NoQamReviewsError(UninferableError):
    """Error when no qam groups still need a review."""

    def __init__(self, accepted_reviews):
        """Create new error for accepted reviews."""
        message = "No 'qam'-groups need review."
        from oscqam.models.review import GroupReview

        accept_reviews = [
            review for review in accepted_reviews if isinstance(review, GroupReview)
        ]
        message += (
            (
                " The following groups were already assigned/finished: {msg}".format(
                    msg=", ".join(
                        ["{r.reviewer}".format(r=review) for review in accept_reviews]
                    )
                )
            )
            if accept_reviews
            else ""
        )
        super().__init__(message)


class NonMatchingGroupsError(UninferableError):
    _msg = (
        "Expected groups and found groups don't match: "
        "Expected: {eg}, found-groups: {fg}."
    )

    def __init__(self, expected_groups, found_groups):
        message = self._msg.format(
            eg=[g.name for g in expected_groups],
            fg=[r.name for r in found_groups],
        )
        super().__init__(message)


class NonMatchingUserGroupsError(UninferableError):
    """Error when the user is not a member of a group that still needs to review
    the request.

    """

    _msg = (
        "User groups and required groups don't match: "
        "User-groups: {ug}, required-groups: {og}."
    )

    def __init__(self, user, user_groups, open_groups):
        message = self._msg.format(
            user=user,
            ug=[g.name for g in user_groups],
            og=[r.name for r in open_groups],
        )
        super().__init__(message)


class InvalidRequestError(ReportedError):
    """Raise when a request object is missing required information."""

    def __init__(self, request):
        super(InvalidRequestError, self).__init__(
            "Invalid build service request: {0}".format(request)
        )


class MissingSourceProjectError(InvalidRequestError):
    """Raise when a request is missing the source project property."""

    def __init__(self, request):
        super().__init__(
            "Invalid build service request: {0} has no source project.".format(request)
        )


class TemplateNotFoundError(ReportedError):
    """Raise when a template could not be found."""

    def __init__(self, message):
        super().__init__("Report could not be loaded: {0}".format(message))


class TestResultMismatchError(ReportedError):
    _msg = "Request-Status not '{0}': please check report: {1}"

    def __init__(self, expected, log_path):
        super().__init__(self._msg.format(expected, log_path))


class ActionError(ReportedError):
    """General error to raise when an error occurred while performing one of the
    actions.

    """


class NoReviewError(UninferableError):
    """Error to raise when a user attempts an unassign action for a request he did
    not start a review for.

    """

    def __init__(self, user):
        super().__init__("User {u} is not assigned for any groups.".format(u=user))


class MultipleReviewsError(UninferableError):
    """Error to raise when a user attempts an unassign action for a request he is
    reviewing for multiple groups at once.

    """

    def __init__(self, user, groups):
        super().__init__(
            "User {u} is currently reviewing for mulitple groups: {g}."
            "Please provide which group to unassign via -G parameter.".format(
                u=user, g=groups
            )
        )


class ReportNotYetGeneratedError(ReportedError):
    _msg = (
        "The report for request '{0}' is not generated yet. "
        "To prevent bugs in the template parser, assigning "
        "is not yet possible. "
        "You can also inspect the server log at {1}"
    )

    def __init__(self, request, log_path):
        super().__init__(
            self._msg.format(
                str(request), log_path.replace("/testreports/", "/reports/")
            )
        )


class OneGroupAssignedError(ReportedError):
    _msg = (
        "User {user} is already assigned for group {group}. "
        "Assigning for multiple groups at once is currently not allowed "
        "to prevent inconsistent states in the build service."
    )

    def __init__(self, assignment):
        super().__init__(
            self._msg.format(user=str(assignment.user), group=str(assignment.group))
        )


class NotPreviousReviewerError(ReportedError):
    _msg = (
        "This request was previously rejected and you were not part "
        "of the previous set of reviewers: {reviewers}."
    )

    def __init__(self, reviewers):
        super().__init__(self._msg.format(reviewers=reviewers))


class NoCommentError(ReportedError):
    _msg = "The request you want to reject must have a comment set in the testreport."

    def __init__(self):
        super().__init__(self._msg)


class NotAssignedError(ReportedError):
    _msg = "The user {user} is not assigned to this update."

    def __init__(self, user):
        super().__init__(self._msg.format(user=user))


class ConflictingOptions(ReportedError):
    pass


class NoCommentsError(ReportedError):
    def __init__(self):
        super().__init__("No comments were found.")


class MissingCommentError(ReportedError):
    def __init__(self):
        super().__init__("Missing comment")


class InvalidCommentIdError(ReportedError):
    def __init__(self, rid, comments):
        msg = "Id {0} is not in valid ids: {1}".format(
            rid, ", ".join([c.id for c in comments])
        )
        super().__init__(msg)

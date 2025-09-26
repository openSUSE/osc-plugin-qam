"""Provides an action to reject a request."""

import sys

from ..errors import NoCommentError
from ..models import Template
from .oscaction import OscAction


class RejectAction(OscAction):
    """Reject a request for a user and group.

    Attempts to automatically find the group that the user assigned himself
    for and will reject that group if possible.

    Attributes:
        DECLINE_MSG: The message to use when declining a request.
        request: The request to reject.
        reason: The reason for rejecting the request.
        message: A message to include with the rejection.
        force: A boolean indicating whether to force the rejection.
    """

    DECLINE_MSG = "Declining request {request} for {user}. See Testreport: {url}"

    def __init__(
        self, remote, user, request_id, reason, force, message=None, out=sys.stdout
    ):
        """Initializes a RejectAction.

        Args:
            remote: A remote facade.
            user: The user rejecting the request.
            request_id: The ID of the request to reject.
            reason: The reason for rejecting the request.
            force: A boolean indicating whether to force the rejection.
            message: A message to include with the rejection.
            out: A file-like object to print messages to.
        """
        super(RejectAction, self).__init__(remote, user, out=out)
        self.request = remote.requests.by_id(request_id)
        self._template = None if not force else "There is no template"
        self.reason = reason
        self.message = message
        self.force: bool = force

    @property
    def template(self):
        """The template for the request."""
        if not self._template:
            self._template = Template(self.request)
        return self._template

    def validate(self):
        """Check preconditions to be met before a request can be approved.

        Raises:
            TestResultMismatchError: if conditions are not met.
            NoCommentError: If no comment is found in the template.
        """
        self.template.failed()
        if not self.template.log_entries["comment"]:
            raise NoCommentError()

    def action(self):
        """Performs the rejection action."""
        if not self.force:
            self.validate()
            url = self.template.fancy_url
        else:
            url = self.template
        msg = RejectAction.DECLINE_MSG.format(
            user=self.user, request=self.request, url=url
        )
        self.print(msg)
        self.request.review_decline(user=self.user, comment=msg, reasons=self.reason)

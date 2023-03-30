import sys

from ..errors import NoCommentError
from ..models import Template
from .oscaction import OscAction


class RejectAction(OscAction):
    """Reject a request for a user and group.

    Attempts to automatically find the group that the user assigned himself
    for and will reject that group if possible.

    """

    DECLINE_MSG = "Declining request {request} for {user}. See Testreport: {url}"

    def __init__(
        self, remote, user, request_id, reason, force, message=None, out=sys.stdout
    ):
        super(RejectAction, self).__init__(remote, user, out=out)
        self.request = remote.requests.by_id(request_id)
        self._template = None if not force else "There is no template"
        self.reason = reason
        self.message = message
        self.force: bool = force

    @property
    def template(self):
        if not self._template:
            self._template = Template(self.request)
        return self._template

    def validate(self):
        """Check preconditions to be met before a request can be approved.

        :raises: :class:`oscqam.models.TestResultMismatchError` if conditions
            are not met.

        """
        self.template.failed()
        if not self.template.log_entries["comment"]:
            raise NoCommentError()

    def action(self):
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

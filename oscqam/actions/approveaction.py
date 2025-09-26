"""Provides a base class for approval actions."""

from .oscaction import OscAction
import abc
import sys
from ..models import Template


class ApproveAction(OscAction):
    """Template class for Approval actions.

    Subclasses need to overwrite:

    - get_reviewer: whose review is done.

    Attributes:
        request: The request to approve.
        template: The template to use for the approval message.
        reviewer: The reviewer to approve the request for.
    """

    def __init__(
        self,
        remote,
        user,
        request_id,
        reviewer,
        template_skip: bool,
        template_factory=Template,
        out=sys.stdout,
    ):
        """Approve a review for either a User or a Group.

        Args:
            remote: Remote interface for build service calls.
            user: The user performing this action.
            request_id: Id of the request to accept.
            reviewer: Reviewer to accept this request for.
            template_skip: If True, do not use a template.
            template_factory: Function to get a report-template from.
            out: File like object to write output messages to.
        """
        super().__init__(remote, user, out)
        self.request = remote.requests.by_id(request_id)
        if template_skip:
            self.template = None
        else:
            self.template = self.request.get_template(template_factory)
        self.reviewer = self.get_reviewer(reviewer)

    @abc.abstractmethod
    def get_reviewer(self, reviwer):
        """Return the object for the given reviewer.

        Args:
            reviwer: The reviewer to get the object for.

        Returns:
            The reviewer object.
        """
        pass

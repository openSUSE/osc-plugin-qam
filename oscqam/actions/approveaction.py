from .oscaction import OscAction
import abc
import sys
from ..models import Template


class ApproveAction(OscAction):
    """Template class for Approval actions.

    Subclasses need to overwrite:

    - get_reviewer: whose review is done.
    """

    def __init__(
        self,
        remote,
        user,
        request_id,
        reviewer,
        template_factory=Template,
        out=sys.stdout,
    ):
        """Approve a review for either a User or a Group.

        :param remote: Remote interface for build service calls.
        :type remote: L{oscqam.remote.RemoteFacade}

        :param user: The user performing this action.
        :type user: L{string}

        :param request_id: Id of the request to accept.
        :type request_id: L{int}

        :param reviewer: Reviewer to accept this request for.
        :type reviewer: L{oscqam.models.User} | L{oscqam.models.Group}

        :param template_factory: Function to get a report-template from.
        :type template_factory:

        :param out: File like object to write output messages to.
        :type out:
        """
        super().__init__(remote, user, out)
        self.request = remote.requests.by_id(request_id)
        self.template = self.request.get_template(template_factory)
        self.reviewer = self.get_reviewer(reviewer)

    @abc.abstractmethod
    def get_reviewer(self, reviwer):
        """Return the object for the given reviewer."""
        pass

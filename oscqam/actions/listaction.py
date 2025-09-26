"""Provides a base class for actions that operate on a list of requests."""

import abc
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from ..errors import TemplateNotFoundError
from ..fields import ReportField
from ..models import Template
from ..utils import multi_level_sort
from .oscaction import OscAction
from .report import Report


class ListAction(OscAction):
    """Base action for operation that work on a list of requests.

    Subclasses must overwrite the 'load_requests' method that return the list
    of requests that should be output according to the formatter and fields.

    Attributes:
        default_fields: A list of fields to display by default.
        template_factory: A function to create a template.
        reports: A list of reports.
    """

    default_fields = [
        ReportField.review_request_id,
        ReportField.srcrpms,
        ReportField.rating,
        ReportField.products,
        ReportField.incident_priority,
    ]

    def group_sort_reports(self):
        """Sort reports according to rating and request id.

        First sort by Priority, then rating and finally request id.
        """
        reports = filter(None, self.reports)
        self.reports = multi_level_sort(
            reports,
            [
                lambda l: l.request.reqid,
                lambda l: l.template.log_entries["Rating"],
                lambda l: l.request.incident_priority,
            ],
        )

    def __init__(self, remote, user, template_factory=Template):
        """Initializes a ListAction.

        Args:
            remote: A remote facade.
            user: The user performing the action.
            template_factory: A function to create a template.
        """
        super().__init__(remote, user)
        self.template_factory = template_factory

    def action(self):
        """Return all reviews that match the parameters of the RequestAction.

        Returns:
            A list of reports.
        """
        self.reports = self._load_listdata(self.load_requests())
        self.group_sort_reports()
        return self.reports

    @abc.abstractmethod
    def load_requests(self):
        """Load requests this class should operate on.

        Returns:
            A list of requests.
        """
        pass

    def merge_requests(self, user_requests, group_requests):
        """Merge the requests together and set a field 'origin' to determine
        where the request came from.

        Args:
            user_requests: A set of requests from the user.
            group_requests: A set of requests from the group.

        Returns:
            A set of all requests.
        """
        all_requests = user_requests.union(group_requests)
        for request in all_requests:
            request.origin = []
            if request in user_requests:
                request.origin.append(self.user.login)
            if request in group_requests:
                request.origin.extend(request.groups)
        return all_requests

    def _load_listdata(self, requests):
        """Load templates for the given requests.

        Templates that could not be loaded will print a warning (this can
        occur and not be a problem: e.g. the template creation script has not
        yet run).

        Args:
            requests: A list of requests.

        Yields:
            A Report object.
        """
        with ThreadPoolExecutor() as executor:
            results = [
                executor.submit(Report, r, self.template_factory) for r in requests
            ]
        for promise in as_completed(results):
            try:
                yield promise.result()
            except TemplateNotFoundError as e:
                logging.warning(str(e))

"""Provides a class to compose a request with a template."""

from ..fields import ReportField
from ..models import GroupReview


class Report:
    """Composes request with the matching template.

    Provides a method to output a list of keys from requests/templates and
    will dispatch to the correct object.

    Attributes:
        request: The request to report on.
        template: The template associated with the request.
    """

    def __init__(self, request, template_factory):
        """Associate a request with the correct template.

        Args:
            request: The request to report on.
            template_factory: A function to create a template.
        """
        self.request = request
        self.template = request.get_template(template_factory)

    def value(self, field):
        """Return the values for fields.

        Args:
            field: The field to get the value for.

        Returns:
            The value of the field.
        """
        entries = self.template.log_entries
        if field == ReportField.unassigned_roles:
            reviews = (
                review
                for review in self.request.review_list_open()
                if isinstance(review, GroupReview) and review.reviewer.is_qam_group()
            )
            value = sorted(str(r.reviewer) for r in reviews)
        elif field == ReportField.package_streams:
            value = [p for p in self.request.packages]
        elif field == ReportField.assigned_roles:
            roles = self.request.assigned_roles
            value = [str(r) for r in roles]
        elif field == ReportField.incident_priority:
            value = self.request.incident_priority
        elif field == ReportField.comments:
            value = self.request.comments
        elif field == ReportField.creator:
            value = self.request.maker
        elif field == ReportField.issues:
            value = str(len(self.request.issues))
        else:
            value = entries.get(str(field), "")
        return value

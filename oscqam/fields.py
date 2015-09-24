from enum import Enum
from .models import ReportedError


class InvalidFieldsError(ReportedError):
    """Raise when the user wants to output non-existent fields.
    """
    _msg = ("Unknown fields: {0}.  "
            "Valid fields: {1}.")

    def __init__(self, bad_fields):
        super(InvalidFieldsError, self).__init__(
            self._msg.format(", ".join(map(repr, bad_fields)),
                             ", ".join(map(str, ReportFields.all_fields)))
        )


class ReportField(Enum):
    """All possible fields that can be displayed for a review.
    """
    review_request_id = (0, "ReviewRequestID")
    products = (1, "Products")
    srcrpms = (2, "SRCRPMs")
    bugs = (3, "Bugs")
    category = (4, "Category")
    rating = (5, "Rating")
    unassigned_roles = (6, "Unassigned Roles")
    assigned_roles = (7, "Assigned Roles")
    package_streams = (8, "Package-Streams")
    incident_priority = (9, "Incident Priority")

    def __init__(self, enum_id, log_key):
        self.enum_id = enum_id
        self.log_key = log_key

    def __str__(self):
        return self.log_key

    @classmethod
    def from_str(cls, field):
        for f in cls:
            if f.value[1] == field:
                return f
        raise InvalidFieldsError([field])


class ReportFields(object):
    all_fields = [ReportField.review_request_id,
                  ReportField.products,
                  ReportField.srcrpms,
                  ReportField.bugs,
                  ReportField.category,
                  ReportField.rating,
                  ReportField.unassigned_roles,
                  ReportField.assigned_roles,
                  ReportField.package_streams,
                  ReportField.incident_priority]

    def fields(self, _):
        return self.all_fields

    @staticmethod
    def review_fields_by_opts(opts):
        if opts.verbose:
            return ReportFields()
        elif opts.fields:
            return UserFields(opts.fields)
        else:
            return DefaultFields()


class DefaultFields(ReportFields):
    def fields(self, action):
        return action.default_fields


class UserFields(ReportFields):
    def __init__(self, fields):
        self._fields = [ReportField.from_str(f) for f in fields]

    def fields(self, _):
        return self._fields

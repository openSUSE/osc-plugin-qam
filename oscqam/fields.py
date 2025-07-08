from enum import Enum

from .errors import ReportedError


def levenshtein(first, second):
    """Calculate levenshtein distance between two strings.

    Deletion, insertion and substitution all have a cost of 1.

    :type first: str
    :type second: str

    :returns: Distance between the strings.
    """
    first = " " + first
    second = " " + second
    rows, cols = (len(first), len(second))
    matrix = [[0] * cols for _ in range(rows)]
    # Set the axis
    for row in range(rows):
        matrix[row][0] = row
    for col in range(cols):
        matrix[0][col] = col

    for row in range(rows):
        for col in range(cols):
            if first[row] == second[col]:
                matrix[row][col] = matrix[row - 1][col - 1]
            else:
                matrix[row][col] = min(
                    matrix[row - 1][col] + 1,
                    matrix[row][col - 1] + 1,
                    matrix[row - 1][col - 1] + 1,
                )
    return matrix[rows - 1][cols - 1]


class InvalidFieldsError(ReportedError):
    """Raise when the user wants to output non-existent fields."""

    _msg = "Unknown fields: {0}. " "Did you mean: {1}. " "(Available fields: {2})"

    def __init__(self, bad_fields):
        suggestions = self._get_suggestions(bad_fields)
        super().__init__(
            self._msg.format(
                ", ".join(map(repr, bad_fields)),
                ", ".join(suggestions),
                ", ".join(map(str, ReportField)),
            )
        )

    def _get_suggestions(self, bad_fields):
        suggestions = set()
        for bad_field in bad_fields:
            distances = [
                (str(field), levenshtein(str(field), bad_field))
                for field in ReportField
            ]
            nearest = min(distances, key=lambda d: d[1])
            suggestions.add(nearest[0])
        return suggestions


class ReportField(Enum):
    """All possible fields that can be displayed for a review."""

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
    comments = (10, "Comments")
    creator = (11, "Creator")
    issues = (12, "Issues")

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


class ReportFields:
    all_fields = [
        ReportField.review_request_id,
        ReportField.products,
        ReportField.srcrpms,
        ReportField.bugs,
        ReportField.category,
        ReportField.rating,
        ReportField.unassigned_roles,
        ReportField.assigned_roles,
        ReportField.package_streams,
        ReportField.incident_priority,
        ReportField.comments,
        ReportField.creator,
        ReportField.issues,
    ]

    def fields(self, action):
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

    def fields(self, action):
        return self._fields

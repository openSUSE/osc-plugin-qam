from .models import ReportedError


class InvalidFieldsError(ReportedError):
    """Raise when the user wants to output non-existent fields.
    """
    _msg = ("Unknown fields: {0}.  "
            "Valid fields: {1}.")

    def __init__(self, bad_fields):
        super(InvalidFieldsError, self).__init__(
            self._msg.format(", ".join(map(repr, bad_fields)),
                             ", ".join(map(repr, ReportFields.all_fields)))
        )


class ReportFields(object):
    all_fields = ["ReviewRequestId",
                  "Products",
                  "SRCRPMs",
                  "Bugs",
                  "Category",
                  "Rating",
                  "Unassigned Roles",
                  "Assigned Roles",
                  "Package-Streams",
                  "Incident Priority"]

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
        badcols = set(fields) - set(self.all_fields)
        if len(badcols):
            raise InvalidFieldsError(badcols)
        self._fields = fields

    def fields(self, _):
        return self._fields

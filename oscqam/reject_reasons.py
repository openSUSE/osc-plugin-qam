"""Implement the possible reject reasons as an enum:


"""
from enum import Enum
from .errors import ReportedError


class InvalidRejectError(ReportedError):
    """Raise when the user wants to output non-existent fields."""

    _msg = "Unknown fields: {0}. " "(Available fields: {1})"

    def __init__(self, bad_fields):
        super(InvalidRejectError, self).__init__(
            self._msg.format(
                ", ".join(map(repr, bad_fields)),
                ", ".join(r.flag for r in RejectReason),
            )
        )


class RejectReason(Enum):
    administrative = (
        0,
        "admin",
        "Administrative " "(e.g. pack more fixes into the updates)",
    )
    retracted = (1, "retracted", "Retracted " "(e.g. fix not needed)")
    build_problem = (
        2,
        "build_problem",
        "Build problem " "(e.g. wrong rpm $version-$release)",
    )
    not_fixed = (
        3,
        "not_fixed",
        "Issues not fixed " "(e.g. incomplete back-port or upstream fix)",
    )
    regression = (
        4,
        "regression",
        "Regression " "(e.g. run-time regression or installation issues)",
    )
    false_reject = (
        5,
        "false_reject",
        "False reject " "(e.g. spoiled results due to test setup error)",
    )
    tracking_issue = (
        6,
        "tracking_issue",
        "Incident tracking issue "
        "(e.g. bad bug list or issues with patchinfo metadata)",
    )

    def __init__(self, enum_id, flag, text):
        """
        :param enum_id: Id of the enum.
        :type enum_id: int

        :param flag: Command line flag to specify the reason.
        :type enum_id: str

        :param text: Explanation text for the value.
        :type text: str
        """
        self.enum_id = enum_id
        self.flag = flag
        self.text = text

    def __str__(self):
        return self.text

    @classmethod
    def from_str(cls, field):
        for f in cls:
            if f.value[1] == field:
                return f
        raise InvalidRejectError([field])

    @classmethod
    def from_id(cls, id):
        ids = [e.enum_id for e in RejectReason]
        for f in cls:
            if f.value[0] == id:
                return f
        raise ValueError(
            "Enum for id not found {0}. " "Valid ids: {1} ".format(id, ids)
        )

"""Implements an enum for the possible reject reasons."""

from enum import Enum
from .errors import ReportedError


class InvalidRejectError(ReportedError):
    """Raise when the user wants to output non-existent fields."""

    _msg = "Unknown fields: {0}. (Available fields: {1})"

    def __init__(self, bad_fields):
        """Initializes an InvalidRejectError.

        Args:
            bad_fields: A list of invalid fields.
        """
        super(InvalidRejectError, self).__init__(
            self._msg.format(
                ", ".join(map(repr, bad_fields)),
                ", ".join(r.flag for r in RejectReason),
            )
        )


class RejectReason(Enum):
    """An enum for the possible reject reasons.

    Attributes:
        enum_id: The integer ID of the enum member.
        flag: The command-line flag for the reason.
        text: The explanation text for the reason.
    """

    administrative = (
        0,
        "admin",
        "Administrative (e.g. pack more fixes into the updates)",
    )
    retracted = (1, "retracted", "Retracted (e.g. fix not needed)")
    build_problem = (
        2,
        "build_problem",
        "Build problem (e.g. wrong rpm $version-$release)",
    )
    not_fixed = (
        3,
        "not_fixed",
        "Issues not fixed (e.g. incomplete back-port or upstream fix)",
    )
    regression = (
        4,
        "regression",
        "Regression (e.g. run-time regression or installation issues)",
    )
    false_reject = (
        5,
        "false_reject",
        "False reject (e.g. spoiled results due to test setup error)",
    )
    tracking_issue = (
        6,
        "tracking_issue",
        "Incident tracking issue (e.g. bad bug list or issues with patchinfo metadata)",
    )

    def __init__(self, enum_id, flag, text):
        """Initializes a RejectReason.

        Args:
            enum_id: Id of the enum.
            flag: Command line flag to specify the reason.
            text: Explanation text for the value.
        """
        self.enum_id = enum_id
        self.flag = flag
        self.text = text

    def __str__(self):
        """Returns the string representation of the reason.

        Returns:
            The explanation text for the reason.
        """
        return self.text

    @classmethod
    def from_str(cls, field):
        """Gets a RejectReason from a string.

        Args:
            field: The string to convert to a RejectReason.

        Returns:
            A RejectReason object.

        Raises:
            InvalidRejectError: If the string does not match any reason.
        """
        for f in cls:
            if f.value[1] == field:
                return f
        raise InvalidRejectError([field])

    @classmethod
    def from_id(cls, id):
        """Gets a RejectReason from an ID.

        Args:
            id: The ID to convert to a RejectReason.

        Returns:
            A RejectReason object.

        Raises:
            ValueError: If the ID does not match any reason.
        """
        ids = [e.enum_id for e in RejectReason]
        for f in cls:
            if f.value[0] == id:
                return f
        raise ValueError("Enum for id not found {0}. Valid ids: {1} ".format(id, ids))

"""
This module contains all models that are required by the QAM plugin to keep
everything in a consistent state.

"""

import osc.core

from .assignment import Assignment
from .attribute import Attribute
from .bug import Bug
from .comment import Comment
from .group import Group
from .request import Request
from .requestfilters import RequestFilter
from .review import GroupReview, UserReview
from .template import Template
from .user import User

__all__ = [
    "Assignment",
    "Attribute",
    "Bug",
    "Comment",
    "Group",
    "GroupReview",
    "Request",
    "RequestFilter",
    "Template",
    "User",
    "UserReview",
]


def monkeypatch():
    """Monkey patch retaining of history into the review class."""

    def monkey_patched_init(obj, review_node):
        # logging.debug("Monkeypatched init")
        original_init(obj, review_node)
        obj.statehistory = []
        for hist_state in review_node.findall("history"):
            obj.statehistory.append(osc.core.RequestHistory(hist_state))

    # logging.warn("Careful - your osc-version requires monkey patching.")
    original_init = osc.core.ReviewState.__init__
    # Deliberate runtime monkeypatch of a third-party class to retain review
    # history; the replacement intentionally differs from the original
    # signature, so the type checker's assignment check does not apply here.
    osc.core.ReviewState.__init__ = monkey_patched_init  # ty: ignore[invalid-assignment]


monkeypatch()

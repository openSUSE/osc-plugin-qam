"""
This module contains all models that are required by the QAM plugin to keep
everything in a consistent state.

"""


import osc.core

from .attribute import Attribute
from .bug import Bug
from .comment import Comment
from .group import Group
from .request import Request
from .requestfilters import RequestFilter
from .review import UserReview
from .review import GroupReview
from .template import Template
from .user import User
from .assignment import Assignment

__all__ = [
    "Assignment",
    "Template",
    "UserReview",
    "GroupReview",
    "Request",
    "Bug",
    "RequestFilter",
    "User",
    "Group",
    "Comment",
    "Attribute",
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
    osc.core.ReviewState.__init__ = monkey_patched_init


monkeypatch()

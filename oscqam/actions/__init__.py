"""A collection of actions that can be performed on requests."""

from .approvegrpoupaction import ApproveGroupAction
from .approveuseraction import ApproveUserAction
from .assignaction import AssignAction
from .commentaction import CommentAction
from .deletecommentaction import DeleteCommentAction
from .infoaction import InfoAction
from .listassignedaction import ListAssignedAction
from .listassignedgroupaction import ListAssignedGroupAction
from .listassigneduseraction import ListAssignedUserAction
from .listgroupaction import ListGroupAction
from .listopenaction import ListOpenAction
from .rejectaction import RejectAction
from .unassignaction import UnassignAction

PREFIX = "[oscqam]"

__all__ = [
    "PREFIX",
    "AssignAction",
    "ApproveGroupAction",
    "ApproveUserAction",
    "ListOpenAction",
    "ListGroupAction",
    "ListAssignedAction",
    "ListAssignedGroupAction",
    "ListAssignedUserAction",
    "UnassignAction",
    "RejectAction",
    "CommentAction",
    "InfoAction",
    "DeleteCommentAction",
]

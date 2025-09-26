"""Provides a base class for actions that interface with the build service."""

import abc
import os
import sys

from ..remotes import RemoteError


class OscAction(metaclass=abc.ABCMeta):
    """Base class for actions that need to interface with the open build service.

    Attributes:
        remote: A remote facade.
        user: The user performing the action.
        undo_stack: A list of actions to perform on rollback.
        out: A file-like object to print messages to.
    """

    def __init__(self, remote, user, out=sys.stdout):
        """Initializes an OscAction.

        Args:
            remote: Remote endpoint to the buildservice.
            user: Username that performs the action.
            out: Filelike to print enduser-messages to.
        """
        self.remote = remote
        self.user = remote.users.by_name(user)
        self.undo_stack = []
        self.out = out

    def __call__(self, *args, **kwargs):
        """Will attempt the encapsulated action and call the rollback function if an
        Error is encountered.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The result of the action, or None if an error occurred.
        """
        try:
            return self.action(*args, **kwargs)
        except RemoteError as e:
            print(str(e))
            self.rollback()

    @abc.abstractmethod
    def action(self, *args, **kwargs):
        """The main action to perform.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        pass

    def rollback(self):
        """Rolls back any actions performed by this action."""
        for action in self.undo_stack:
            action()

    def print(self, msg, end=os.linesep):
        """Mimick the print-statements behaviour on the out-stream:

        Print the given message and add a newline.

        Args:
            msg: The message to print.
            end: The line ending to use.
        """
        self.out.write(msg)
        self.out.write(end)
        self.out.flush()

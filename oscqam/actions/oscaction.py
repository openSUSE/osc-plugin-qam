import abc
import os
import sys

from ..remotes import RemoteError


class OscAction(metaclass=abc.ABCMeta):
    """Base class for actions that need to interface with the open build service."""

    def __init__(self, remote, user, out=sys.stdout):
        """
        :param remote: Remote endpoint to the buildservice.
        :type remote: :class:`oscqam.models.RemoteFacade`

        :param user: Username that performs the action.
        :type user: str

        :param out: Filelike to print enduser-messages to.
        :type out: :class:`file`
        """
        self.remote = remote
        self.user = remote.users.by_name(user)
        self.undo_stack = []
        self.out = out

    def __call__(self, *args, **kwargs):
        """Will attempt the encapsulated action and call the rollback function if an
        Error is encountered.

        """
        try:
            return self.action(*args, **kwargs)
        except RemoteError as e:
            print(str(e))
            self.rollback()

    @abc.abstractmethod
    def action(self, *args, **kwargs):
        pass

    def rollback(self):
        for action in self.undo_stack:
            action()

    def print(self, msg, end=os.linesep):
        """Mimick the print-statements behaviour on the out-stream:

        Print the given message and add a newline.

        :type msg: str
        """
        self.out.write(msg)
        self.out.write(end)
        self.out.flush()

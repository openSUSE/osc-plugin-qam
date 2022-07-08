import abc


class Reviewer(metaclass=abc.ABCMeta):
    """Superclass for possible reviewer-classes."""

    @abc.abstractmethod
    def is_qam_group(self):
        """
        :returns: True if the group denotes reviews it's associated with to
            be reviewed by a QAM member.

        """
        pass

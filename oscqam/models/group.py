"""Represents a group in the build service."""

from .filters import GroupFilter
from .reviewer import Reviewer
from .xmlfactorymixin import XmlFactoryMixin


class Group(XmlFactoryMixin, Reviewer):
    """A group object from the build service.

    Attributes:
        remote: A remote facade.
        filter: A group filter object.
        name: The name of the group.
    """

    def __init__(self, remote, attributes, children):
        """Initializes a Group.

        Args:
            remote: A remote facade.
            attributes: A dictionary of attributes for the XML element.
            children: A dictionary of child elements for the XML element.
        """
        super().__init__(remote, attributes, children)
        self.remote = remote
        self.filter = GroupFilter.for_remote(remote)
        if "title" in children:
            # We set name to title to ensure equality.  This allows us to
            # prevent having to query *all* groups we need via this method,
            # which could use very many requests.
            self.name = children["title"]

    @classmethod
    def parse(cls, remote, xml):
        """Parses a group from XML.

        Args:
            remote: A remote facade.
            xml: The XML to parse.

        Returns:
            A Group object.
        """
        return super(Group, cls).parse(remote, xml, "group")

    @classmethod
    def parse_entry(cls, remote, xml):
        """Parses a group from a directory entry XML.

        Args:
            remote: A remote facade.
            xml: The XML to parse.

        Returns:
            A Group object.
        """
        return super(Group, cls).parse(remote, xml, "entry")

    def is_qam_group(self):
        """Checks if the group is a QAM group.

        'qam-auto' is already used to designate automated reviews:
        It is excluded here, as it does not require manual review
        by a QAM member.

        Returns:
            True if the group is a QAM group, False otherwise.
        """
        return self.filter.is_qam_group(self)

    def __hash__(self):
        """Returns a hash for the group.

        We don't want to hash to the same as only the string.

        Returns:
            An integer hash value.
        """
        return hash(self.name) + hash(type(self))

    def __eq__(self, other):
        """Checks if two groups are equal.

        Args:
            other: The other group to compare to.

        Returns:
            True if the groups are equal, False otherwise.
        """
        if not isinstance(other, Group):
            return False
        return self.name == other.name

    def __str__(self):
        """Returns a string representation of the group.

        Returns:
            The name of the group.
        """
        return "{0}".format(self.name)

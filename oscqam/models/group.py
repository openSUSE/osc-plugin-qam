from .filters import GroupFilter
from .reviewer import Reviewer
from .xmlfactorymixin import XmlFactoryMixin


class Group(XmlFactoryMixin, Reviewer):
    """A group object from the build service."""

    def __init__(self, remote, attributes, children):
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
        return super(Group, cls).parse(remote, xml, "group")

    @classmethod
    def parse_entry(cls, remote, xml):
        return super(Group, cls).parse(remote, xml, "entry")

    def is_qam_group(self):
        # 'qam-auto' is already used to designate automated reviews:
        # It is excluded here, as it does not require manual review
        # by a QAM member.
        return self.filter.is_qam_group(self)

    def __hash__(self):
        # We don't want to hash to the same as only the string.
        return hash(self.name) + hash(type(self))

    def __eq__(self, other):
        if not isinstance(other, Group):
            return False
        return self.name == other.name

    def __str__(self):
        return "{0}".format(self.name)

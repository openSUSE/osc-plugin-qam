from .xmlfactorymixin import XmlFactoryMixin


class NullComment:
    """Null-Object for comments."""

    def __init__(self):
        self.id = None
        self.text = None

    def __str__(self):
        return ""


class Comment(XmlFactoryMixin):
    none = NullComment()

    def delete(self):
        self.remote.comments.delete(self)

    @classmethod
    def parse(cls, remote, xml):
        return super(Comment, cls).parse(remote, xml, "comment")

    def __str__(self):
        return "{0}: {1}".format(self.id, self.text)

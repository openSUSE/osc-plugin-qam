"""Represents a comment on a request."""

from .xmlfactorymixin import XmlFactoryMixin


class NullComment:
    """A null object for comments.

    This is used to represent the absence of a comment.

    Attributes:
        id: The ID of the comment (always None).
        text: The text of the comment (always None).
    """

    def __init__(self):
        """Initializes a NullComment."""
        self.id = None
        self.text = None

    def __str__(self):
        """Returns an empty string."""
        return ""


class Comment(XmlFactoryMixin):
    """Represents a comment on a request.

    Attributes:
        none: A NullComment object.
        id: The ID of the comment.
        text: The text of the comment.
    """

    none = NullComment()

    def delete(self):
        """Deletes the comment."""
        self.remote.comments.delete(self)

    @classmethod
    def parse(cls, remote, xml):
        """Parses a comment from XML.

        Args:
            remote: A remote facade.
            xml: The XML to parse.

        Returns:
            A Comment object.
        """
        return super(Comment, cls).parse(remote, xml, "comment")

    def __str__(self):
        """Returns a string representation of the comment.

        Returns:
            A string in the format "id: text".
        """
        return "{0}: {1}".format(self.id, self.text)

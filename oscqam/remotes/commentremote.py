"""Provides a class for interacting with comments on the remote."""

from ..models import Comment


class CommentRemote:
    """Interacts with comments on the remote.

    Attributes:
        endpoint: The API endpoint for comments.
        delete_endpoint: The API endpoint for deleting comments.
        remote: A remote facade.
    """

    endpoint = "comments"
    delete_endpoint = "comment"

    def __init__(self, remote):
        """Initializes a CommentRemote.

        Args:
            remote: A remote facade.
        """
        self.remote = remote

    def for_request(self, request):
        """Gets the comments for a given request.

        Args:
            request: The request to get comments for.

        Returns:
            A list of Comment objects.
        """
        endpoint = "{0}/request/{1}".format(self.endpoint, request.reqid)
        xml = self.remote.get(endpoint)
        return Comment.parse(self.remote, xml)

    def delete(self, comment_id):
        """Deletes a comment.

        Args:
            comment_id: The ID of the comment to delete.
        """
        endpoint = "{0}/{1}".format(self.delete_endpoint, comment_id)
        self.remote.delete(endpoint)

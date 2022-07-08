from ..models import Comment


class CommentRemote:
    endpoint = "comments"
    delete_endpoint = "comment"

    def __init__(self, remote):
        self.remote = remote

    def for_request(self, request):
        endpoint = "{0}/request/{1}".format(self.endpoint, request.reqid)
        xml = self.remote.get(endpoint)
        return Comment.parse(self.remote, xml)

    def delete(self, comment_id):
        endpoint = "{0}/{1}".format(self.delete_endpoint, comment_id)
        self.remote.delete(endpoint)

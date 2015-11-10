from __future__ import print_function
from collections import defaultdict
from .utils import load_fixture
from oscqam.remotes import CommentRemote, RequestRemote, GroupRemote, UserRemote


class MockRemote(object):
    """Replacement for L{oscqam.models.Remote} that maps HTTP requests to
    file-paths.

    The mapping between a request and filepath is determined by the requested
    URL: the last part of the url is expected to be the identifier, the
    previous part to the object-type.

    Files should be named accordingly: {object_type}_{identifier}.xml

    """
    def __init__(self):
        self.delete_calls = []
        self.post_calls = []
        self.overrides = defaultdict(dict)
        self.requests = RequestRemote(self)
        self.groups = GroupRemote(self)
        self.users = UserRemote(self)
        self.comments = CommentRemote(self)

    def _load(self, prefix, id):
        name = "%s_%s.xml" % (prefix, id)
        return load_fixture(name)

    def _encode_args(self, *args):
        if args:
            return repr(args)
        return "None"

    def get(self, *args, **kwargs):
        """Replacement for HTTP-get requests.

        Will first check if the requested URL is registered as an override.
        If so the override-data will be returned, otherwise the URL will
        be mapped to the filesystem storage for test-fixtures.
        """
        url = args[0]
        args = args[1:]
        if url in self.overrides:
            # The first arg is the endpoint.
            enc = self._encode_args(*args)
            if enc in self.overrides[url]:
                return self.overrides[url][enc]()
        try:
            cls, identifier = url.split("/", 1)
        except ValueError:
            if url == 'group':
                cls = 'group'
                identifier = args[0]['login']
            else:
                raise
        return self._load(cls, identifier)

    def delete(self, *args, **kwargs):
        called = "Call-Args: %s. Call-Kwargs: %s" % (args, kwargs)
        self.delete_calls.append(called)

    def post(self, *args, **kwargs):
        called = "Call-Args: %s. Call-Kwargs: %s" % (args, kwargs)
        self.post_calls.append(called)

    def register_url(self, url, callback, *args):
        """Allow specifying a override for a given relative url.

        :param url: Url that should trigger a callback.
        :type url: str

        :param callback: Function to call when the url is hit.
        :type callback: () -> Either(str | Exception)

        """
        enc = self._encode_args(*args)
        self.overrides[url][enc] = callback

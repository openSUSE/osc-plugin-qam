from __future__ import print_function
from .utils import load_fixture


class MockRemote(object):
    """Replacement for L{oscqam.models.Remote} that maps HTTP requests to
    file-paths.

    The mapping between a request and filepath is determined by the requested
    URL: the last part of the url is expected to be the identifier, the
    previous part to the object-type.

    Files should be named accordingly: {object_type}_{identifier}.xml

    """
    def __init__(self):
        self.post_calls = []
        self.overrides = {}

    def _load(self, prefix, id):
        name = "%s_%s.xml" % (prefix, id)
        return load_fixture(name)

    def get(self, *args, **kwargs):
        """Replacement for HTTP-get requests.

        Will first check if the requested URL is registered as an override.
        If so the override-data will be returned, otherwise the URL will
        be mapped to the filesystem storage for test-fixtures.
        """
        url = args[0]
        if url in self.overrides:
            return self.overrides[url]()
        try:
            cls, identifier = url.split("/", 1)
        except ValueError:
            if args[0] == 'group':
                cls = 'group'
                identifier = args[1]['login']
            else:
                raise
        return self._load(cls, identifier)

    def post(self, *args, **kwargs):
        called = "Call-Args: %s. Call-Kwargs: %s" % (args, kwargs)
        self.post_calls.append(called)

    def register_url(self, url, callback):
        """Allow specifying a override for a given relative url.

        :param url: Url that should trigger a callback.
        :type url: str

        :param callback: Function to call when the url is hit.
        :type callback: () -> Either(str | Exception)

        """
        self.overrides[url] = callback

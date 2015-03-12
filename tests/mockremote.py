from __future__ import print_function
import os

data = os.path.join(os.path.dirname(__file__), 'data')


class MockRemote(object):
    def __init__(self, *args, **kwargs):
        self.post_calls = []

    def _load(self, prefix, id):
        file_name = "%s_%s.xml" % (prefix, id)
        path = "%s/%s" % (data, file_name)
        with open(path, 'r') as f:
            return f.read()

    def get(self, *args, **kwargs):
        try:
            cls, identifier = args[0].split("/")
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

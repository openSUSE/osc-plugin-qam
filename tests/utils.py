import os


path = os.path.join(os.path.dirname(__file__), 'fixtures')


def load_fixture(name):
    return open("%s/%s" % (path, name)).read()

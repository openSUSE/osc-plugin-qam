from collections import OrderedDict
import os
from oscqam.models import TemplateParser


path = os.path.join(os.path.dirname(__file__), 'fixtures')


def load_fixture(name):
    return open("%s/%s" % (path, name)).read()


def create_template_data(**data):
    """Adds missing keys and values to the template data.

    """
    data = OrderedDict(**data)
    if 'comment' not in data.keys():
        data['comment'] = ''
    if '$Author' not in data.keys():
        data['$Author'] = 'none $'
    if TemplateParser.end_marker not in data.keys():
        data[TemplateParser.end_marker] = ''
    return '\n'.join(': '.join(v) for v in
                     (zip(data.keys(), data.values())))

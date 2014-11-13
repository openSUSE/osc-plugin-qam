"""This module contains all models that are required by the QAM plugin to keep
everything in a consistent state.

"""
import logging
import os
import re
import urllib
try:
    from xml.etree import cElementTree as ET
except ImportError:
    import cElementTree as ET
import osc.core
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RemoteFacade(object):
    def __init__(self, remote):
        """Initialize a new RemoteOscRemote that points to the given remote.
        """
        self.remote = remote
        
    def get(self, endpoint, callback, params=None):
        """Retrieve information at the given endpoint with the parameters.

        Call the callback function with the result.

        """
        if params:
            params = urllib.urlencode(params)
        url = '/'.join([self.remote, endpoint])
        remote = osc.core.http_GET(url, data=params)
        xml = remote.read()
        return callback(self, xml)


class XmlFactoryMixin(object):
    """Can generate an object from xml by recursively parsing the structure.

    It will set properties to the text-property of a node if there are no
    children.

    Otherwise it will parse the children into another node and set the property
    to a list of these new parsed nodes.
    """
    def __init__(self, *args, **kwargs):
        """Will set every element in kwargs to a property of the class.
        """
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def exists(self, attr):
        return hasattr(self, attr) and getattr(self, attr)
    
    @staticmethod
    def listify(dictionary, key):
        """Will wrap an existing dictionary key in a list.
        """
        if not isinstance(dictionary[key], list):
            value = dictionary[key]
            del dictionary[key]
            dictionary[key] = [value]

    @classmethod
    def parse_et(cls, remote, et, tag, wrapper_cls=None):
        """Recursively parses an element-tree instance.

        Will iterate over the tag as root-level.
        """
        if not wrapper_cls:
            wrapper_cls = cls
        objects = []
        for request in et.iter(tag):
            attribs = {}
            for attribute in request.attrib:
                attribs[attribute] = request.attrib[attribute]
            kwargs = {}
            for child in request:
                key = child.tag
                subchildren = list(child)
                if subchildren or child.attrib:
                    # Prevent that all children have the same class as the parent.
                    # This might lead to providing methods that make no sense.
                    value = cls.parse_et(remote, child, key, XmlFactoryMixin)
                    if len(value) == 1:
                        value = value[0]
                else:
                    if child.text:
                        value = child.text.strip()
                    else:
                        value = None
                if key in kwargs:
                    XmlFactoryMixin.listify(kwargs, key)
                    kwargs[key].append(value)
                else:
                    kwargs[key] = value
            kwargs.update(attribs)
            objects.append(wrapper_cls(remote, **kwargs))
        return objects
    
    @classmethod
    def parse(cls, remote, xml, tag):
        root = ET.fromstring(xml)
        return cls.parse_et(remote, root, tag, cls)


class Group(XmlFactoryMixin):
    """A group object from the build service.
    """
    endpoint = 'group'
    
    def __init__(self, remote, **kwargs):
        super(Group, self).__init__(**kwargs)
        self.remote = remote

    @classmethod
    def all(cls, remote):
        return remote.get(cls.endpoint, Group.parse)

    @classmethod
    def for_user(cls, remote, user):
        params = {'login': user.login}
        return remote.get(cls.endpoint, Group.parse, params)

    @classmethod
    def parse(cls, remote, xml):
        return super(Group, cls).parse(remote, xml, 'entry')

class User(XmlFactoryMixin):
    """Wraps a user of the obs in an object.

    """
    endpoint = 'person'
    
    def __init__(self, remote, **kwargs):
        super(User, self).__init__(**kwargs)
        self.remote = remote
        self._groups = None
                                    
    @property
    def groups(self):
        """Read-only property for groups a user is part of.
        """
        # Maybe use a invalidating cache as a trade-off between current
        # information and slow response.
        if not self._groups:
            self._groups = Group.for_user(self.remote, self)
        return self._groups

    def __str__(self):
        return unicode(self)

    def __unicode__(self):
        return u"{0} ({1})".format(self.realname, self.email)

    @classmethod
    def by_name(cls, remote, name):
        url = '/'.join([User.endpoint, name])
        users = remote.get(url, User.parse)
        import pdb; pdb.set_trace()
        if users:
            return users[0]
        raise AttributeError("User not found.")

    @classmethod
    def parse(cls, remote, xml):
        return super(User, cls).parse(remote, xml, cls.endpoint)
            

class Request(XmlFactoryMixin):
    endpoint = 'request'
    
    def __init__(self, remote, **kwargs):
        super(Request, self).__init__(**kwargs)
        self.remote = remote

    @property
    def groups(self):
        # Maybe use a invalidating cache as a trade-off between current
        # information and slow response.
        if not self.groups:
            self.groups = Group.for_request(self.remote, self)
        return self.groups

    @classmethod
    def all(cls, remote):
        pass

    @classmethod
    def for_user(cls, remote, user):
        params={'user': user.login,
                'view': 'collection'}
        return remote.get(cls.endpoint, cls.parse, params)

    @classmethod
    def by_id(cls, remote, req_id):
        pass

    @classmethod
    def parse(cls, remote, xml):
        super(Request, cls).parse(remote, xml, cls.endpoint)
        

class Assignment(object):
    """Stores the current association between a user, a group and a request.
    """
    def __init__(self, group, request, user):
        self.group = group
        self.request = request
        self.user = user
        self.state = None

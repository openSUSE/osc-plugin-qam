"""This module contains all models that are required by the QAM plugin to keep
everything in a consistent state.

"""
import osc.core
import urllib
try:
    from xml.etree import cElementTree as ET
except ImportError:
    import cElementTree as ET


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
    @staticmethod
    def listify(dictionary, key):
        """Will wrap an existing dictionary key in a list.
        """
        if not isinstance(dictionary[key], list):
            value = dictionary[key]
            del dictionary[key]
            dictionary[key] = [value]

    @classmethod
    def parse_et(cls, remote, et, tag):
        """Recursively parses an element-tree instance.

        Will iterate over the tag as root-level.
        """
        objects = []
        for request in et.iter(tag):
            kwargs = {}
            for attribute in request:
                key = attribute.tag
                children = attribute.getchildren()
                # Handle nested element
                if children:
                    value = cls.parse_et(remote, attribute, key)
                    if key in kwargs:
                        XmlFactoryMixin.listify(kwargs, key)
                        kwargs[key].append(value)
                    else:
                        kwargs[key] = value
                # TODO: Handle elements with attributes
                else:
                    kwargs[key] = attribute.text
            objects.append(cls(remote, **kwargs))
        return objects
    
    @classmethod
    def parse(cls, remote, xml, tag):
        root = ET.fromstring(xml)
        return cls.parse_et(remote, root, tag)


class Group(XmlFactoryMixin):
    """A group object from the build service.
    """
    endpoint = 'group'
    
    def __init__(self, remote, **kwargs):
        self.remote = remote
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

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
        self.remote = remote
        self._groups = None
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])
                                    
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
        self.remote = remote
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

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

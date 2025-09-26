"""Provides a mixin for creating objects from XML."""

from xml.etree import ElementTree as ET


class XmlFactoryMixin:
    """Can generate an object from xml by recursively parsing the structure.

    It will set properties to the text-property of a node if there are no
    children.

    Otherwise it will parse the children into another node and set the property
    to a list of these new parsed nodes.
    """

    def __init__(self, remote, attributes, children):
        """Will set every element in kwargs to a property of the class.

        Args:
            remote: A remote facade.
            attributes: A dictionary of attributes for the XML element.
            children: A dictionary of child elements for the XML element.
        """
        attributes.update(children)
        for kwarg in attributes:
            setattr(self, kwarg, attributes[kwarg])

    @staticmethod
    def listify(dictionary, key):
        """Will wrap an existing dictionary key in a list.

        Args:
            dictionary: The dictionary to modify.
            key: The key to listify.
        """
        if not isinstance(dictionary[key], list):
            value = dictionary[key]
            del dictionary[key]
            dictionary[key] = [value]

    @classmethod
    def parse_et(cls, remote, et, tag, wrapper_cls=None):
        """Recursively parses an element-tree instance.

        Will iterate over the tag as root-level.

        Args:
            remote: A remote facade.
            et: The element tree to parse.
            tag: The tag to iterate over.
            wrapper_cls: The class to wrap the parsed objects in.

        Returns:
            A list of parsed objects.
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
                    # Prevent that all children have the same class as the
                    # parent.  This might lead to providing methods that make
                    # no sense.
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
            if request.text:
                kwargs["text"] = request.text
            kwargs.update(attribs)
            objects.append(wrapper_cls(remote, attribs, kwargs))
        return objects

    @classmethod
    def parse(cls, remote, xml, tag):
        """Parses an object from XML.

        Args:
            remote: A remote facade.
            xml: The XML to parse.
            tag: The root tag of the object.

        Returns:
            A list of parsed objects.
        """
        root = ET.fromstring(xml)
        return cls.parse_et(remote, root, tag, cls)

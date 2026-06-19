"""Provides a mixin for creating objects from XML."""

from typing import Any
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

    def __getattr__(self, name: str) -> Any:
        """Declares that instances expose attributes populated from XML.

        Instances of this mixin (and its subclasses) receive their attributes
        dynamically in ``__init__`` via :func:`setattr`, based on the parsed XML
        structure. This hook makes those dynamically-set attributes visible to
        static type checkers. It is only invoked for attributes that are not
        found through normal lookup, so it does not interfere with attributes
        that were actually set.

        Args:
            name: The name of the attribute being accessed.

        Raises:
            AttributeError: Always, to preserve normal attribute-error
                semantics for attributes that were never set from XML.
        """
        raise AttributeError(
            f"{type(self).__name__!r} object has no attribute {name!r}"
        )

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
                    existing = kwargs[key]
                    if isinstance(existing, list):
                        existing.append(value)
                    else:
                        kwargs[key] = [existing, value]
                else:
                    kwargs[key] = value
            if request.text:
                kwargs["text"] = request.text
            kwargs.update(attribs)
            objects.append(wrapper_cls(remote, attribs, kwargs))
        return objects

    @classmethod
    def parse(cls, remote, xml, tag=None):
        """Parses an object from XML.

        Args:
            remote: A remote facade.
            xml: The XML to parse.
            tag: The root tag of the object. Subclasses typically supply a
                fixed tag and may ignore any value passed by a caller.

        Returns:
            A list of parsed objects.
        """
        root = ET.fromstring(xml)
        return cls.parse_et(remote, root, tag, cls)

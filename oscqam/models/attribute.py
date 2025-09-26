"""Represents an attribute of a request."""

from xml.etree import ElementTree as ET

from .xmlfactorymixin import XmlFactoryMixin


class Attribute(XmlFactoryMixin):
    """Represents an attribute of a request.

    Attributes:
        reject_reason: A string representing the reject reason attribute.
        value: The value of the attribute.
    """

    reject_reason = "MAINT:RejectReason"

    def __init__(self, remote, attributes, children):
        """Initializes an Attribute.

        Args:
            remote: A remote facade.
            attributes: A dictionary of attributes for the XML element.
            children: A dictionary of child elements for the XML element.
        """
        super().__init__(remote, attributes, children)
        # We expect the value to be a sequence type even if there is only
        # one reasons specified.
        if not isinstance(self.value, (list, tuple)):
            self.value = [self.value]

    @classmethod
    def parse(cls, remote, xml):
        """Parses an attribute from XML.

        Args:
            remote: A remote facade.
            xml: The XML to parse.

        Returns:
            An Attribute object.
        """
        return super(Attribute, cls).parse(remote, xml, "attribute")

    @classmethod
    def preset(cls, remote, preset, *value):
        """Create a new attribute from a default attribute.

        Default attributes are stored as class-variables on this class.

        Args:
            remote: A remote facade.
            preset: The preset attribute to use.
            *value: The value of the attribute.

        Returns:
            An Attribute object.
        """
        namespace, name = preset.split(":")
        return Attribute(
            remote, {"namespace": namespace, "name": name}, {"value": value}
        )

    def __eq__(self, other):
        """Checks if two attributes are equal.

        Args:
            other: The other attribute to compare to.

        Returns:
            True if the attributes are equal, False otherwise.
        """
        if not isinstance(other, Attribute):
            return False
        return (
            self.namespace == other.namespace
            and self.name == other.name
            and self.value == other.value
        )

    def xml(self):
        """Turn this attribute into XML.

        Returns:
            A string containing the XML representation of this attribute.
        """
        root = ET.Element("attribute")
        root.set("name", self.name)
        root.set("namespace", self.namespace)
        for val in self.value:
            value = ET.SubElement(root, "value")
            value.text = val
        return ET.tostring(root)

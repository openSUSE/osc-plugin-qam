from xml.etree import ElementTree as ET

from .xmlfactorymixin import XmlFactoryMixin


class Attribute(XmlFactoryMixin):
    reject_reason = "MAINT:RejectReason"

    def __init__(self, remote, attributes, children):
        super().__init__(remote, attributes, children)
        # We expect the value to be a sequence type even if there is only
        # one reasons specified.
        if not isinstance(self.value, (list, tuple)):
            self.value = [self.value]

    @classmethod
    def parse(cls, remote, xml):
        return super(Attribute, cls).parse(remote, xml, "attribute")

    @classmethod
    def preset(cls, remote, preset, *value):
        """Create a new attribute from a default attribute.

        Default attributes are stored as class-variables on this class.
        """
        namespace, name = preset.split(":")
        return Attribute(
            remote, {"namespace": namespace, "name": name}, {"value": value}
        )

    def __eq__(self, other):
        if not isinstance(other, Attribute):
            return False
        return (
            self.namespace == other.namespace
            and self.name == other.name
            and self.value == other.value
        )

    def xml(self):
        """Turn this attribute into XML."""
        root = ET.Element("attribute")
        root.set("name", self.name)
        root.set("namespace", self.namespace)
        for val in self.value:
            value = ET.SubElement(root, "value")
            value.text = val
        return ET.tostring(root)

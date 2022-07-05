from oscqam import models

from .utils import load_fixture


def test_parse_flat_xml():
    xml = load_fixture("flat.xml")
    persons = models.XmlFactoryMixin.parse(None, xml, "person")
    john = persons[0]
    assert john.firstname == "John"
    assert john.lastname == "Smith"


def test_parse_nested_xml():
    xml = load_fixture("nested.xml")
    persons = models.XmlFactoryMixin.parse(None, xml, "person")
    john = persons[0]
    assert john.firstname == "John"
    assert john.lastname == "Smith"
    assert john.address.streetname == "Arcadiaavenue"
    assert john.address.streetnumber == "1"


def test_parse_nested_xml_multiple():
    xml = load_fixture("nested_multi.xml")
    persons = models.XmlFactoryMixin.parse(None, xml, "person")
    john = persons[0]
    assert john.firstname == "John"
    assert john.lastname == "Smith"
    assert len(john.address) == 2
    assert john.address[0].streetname == "Arcadiaavenue"
    assert john.address[0].streetnumber == "1"
    assert john.address[1].streetname == "Rassilonblvd"
    assert john.address[1].streetnumber == "2"


def test_parse_attributes():
    xml = load_fixture("attributes.xml")
    persons = models.XmlFactoryMixin.parse(None, xml, "person")
    john = persons[0]
    assert john.firstname == "John"
    assert john.lastname == "Smith"


def test_parse_multi_attributes():
    xml = load_fixture("attributes_multi.xml")
    persons = models.XmlFactoryMixin.parse(None, xml, "person")
    john = persons[0]
    assert john.firstname == "John"
    assert john.lastname == "Smith"
    clara = persons[1]
    assert clara.firstname == "Clara"
    assert clara.lastname == "Oswald"


def test_parse_nested_and_attributes():
    xml = load_fixture("nested_attributes.xml")
    persons = models.XmlFactoryMixin.parse(None, xml, "person")
    john = persons[0]
    assert john.id == "1"
    assert john.firstname == "John"
    assert john.lastname == "Smith"
    assert john.address.main == "True"
    assert john.address.streetname == "Arcadiaavenue"
    assert john.address.streetnumber == "1"

#!/usr/bin/env python
import os
import unittest
from oscqam import models


path = os.path.join(os.path.dirname(__file__), 'data')


class XmlFactoryMixinTests(unittest.TestCase):
    """Test automatic parsing code for xml returned from the build service.

    """
    def _load_xml(self, filename):
        absolute_path = os.path.join(path, filename)
        with open(absolute_path, 'r') as xml_file:
            return xml_file.read()

    def test_parse_flat_xml(self):
        xml = self._load_xml("flat.xml")
        persons = models.XmlFactoryMixin.parse(None, xml, 'person')
        john = persons[0]
        self.assertEqual(john.firstname, 'John')
        self.assertEqual(john.lastname, 'Smith')

    def test_parse_nested_xml(self):
        xml = self._load_xml("nested.xml")
        persons = models.XmlFactoryMixin.parse(None, xml, 'person')
        john = persons[0]
        self.assertEqual(john.firstname, 'John')
        self.assertEqual(john.lastname, 'Smith')
        self.assertEqual(john.address.streetname, 'Arcadiaavenue')
        self.assertEqual(john.address.streetnumber, '1')

    def test_parse_nested_xml_multiple(self):
        xml = self._load_xml("nested_multi.xml")
        persons = models.XmlFactoryMixin.parse(None, xml, 'person')
        john = persons[0]
        self.assertEqual(john.firstname, 'John')
        self.assertEqual(john.lastname, 'Smith')
        self.assertEqual(len(john.address), 2)
        self.assertEqual(john.address[0].streetname, 'Arcadiaavenue')
        self.assertEqual(john.address[0].streetnumber, '1')
        self.assertEqual(john.address[1].streetname, 'Rassilonblvd')
        self.assertEqual(john.address[1].streetnumber, '2')

    def test_parse_attributes(self):
        xml = self._load_xml("attributes.xml")
        persons = models.XmlFactoryMixin.parse(None, xml, 'person')
        john = persons[0]
        self.assertEqual(john.firstname, 'John')
        self.assertEqual(john.lastname, 'Smith')

    def test_parse_multi_attributes(self):
        xml = self._load_xml("attributes_multi.xml")
        persons = models.XmlFactoryMixin.parse(None, xml, 'person')
        john = persons[0]
        self.assertEqual(john.firstname, 'John')
        self.assertEqual(john.lastname, 'Smith')
        clara = persons[1]
        self.assertEqual(clara.firstname, 'Clara')
        self.assertEqual(clara.lastname, 'Oswald')

    def test_parse_nested_and_attributes(self):
        xml = self._load_xml("nested_attributes.xml")
        persons = models.XmlFactoryMixin.parse(None, xml, 'person')
        john = persons[0]
        self.assertEqual(john.id, '1')
        self.assertEqual(john.firstname, 'John')
        self.assertEqual(john.lastname, 'Smith')
        self.assertEqual(john.address.main, 'True')
        self.assertEqual(john.address.streetname, 'Arcadiaavenue')
        self.assertEqual(john.address.streetnumber, '1')

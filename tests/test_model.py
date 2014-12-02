import os
import unittest
from xml.etree import ElementTree
from oscqam.models import Request


path = os.path.join(os.path.dirname(__file__), 'data')


class MockRemote(object):
    def get(self, *args, **kwargs):
        pass

    def post(self, *args, **kwargs):
        pass


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.req_1_xml = open(os.path.join(path, 'request_1.xml')).read()
        cls.req_2_xml = open(os.path.join(path, 'request_2.xml')).read()

    def setUp(self):
        self.remote = MockRemote()

    def test_merge_requests(self):
        request_1 = Request.parse(self.remote, self.req_1_xml)[0]
        request_2 = Request.parse(self.remote, self.req_2_xml)[0]
        requests = set([request_1, request_2])
        self.assertEqual(len(requests), 1)

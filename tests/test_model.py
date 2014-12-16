import mock
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
        cls.req_search = open(os.path.join(path, 'request_search.xml')).read()
        cls.req_search_none = open(os.path.join(
            path,
            'request_search_none_proj.xml'
        )).read()
        cls.req_no_src = open(os.path.join(path, 'request_no_src.xml')).read()
        cls.req_assign = open(os.path.join(path, 'request_assign.xml')).read()
        cls.req_unassign = open(os.path.join(
            path, 'request_unassign.xml'
        )).read()

    def setUp(self):
        self.remote = MockRemote()

    def test_merge_requests(self):
        request_1 = Request.parse(self.remote, self.req_1_xml)[0]
        request_2 = Request.parse(self.remote, self.req_2_xml)[0]
        requests = set([request_1, request_2])
        self.assertEqual(len(requests), 1)

    def test_search(self):
        """Only requests that are part of SUSE:Maintenance projects should be
        used.
        """
        requests = Request.parse(self.remote, self.req_search)
        self.assertEqual(len(requests), 2)
        requests = Request.filter_by_project("SUSE:Maintenance", requests)
        self.assertEqual(len(requests), 1)

    def test_search_empty_source_project(self):
        """Projects with empty source project should be handled gracefully.

        """
        requests = Request.parse(self.remote, self.req_search_none)
        requests = Request.filter_by_project("SUSE:Maintenance", requests)
        self.assertEqual(len(requests), 0)

    def test_project_without_source_project(self):
        """When project attribute can be found in a source tag the API should
        just return an empty string and not fail.
        """
        requests = Request.parse(self.remote, self.req_no_src)
        self.assertEqual(requests[0].src_project, '')
        requests = Request.filter_by_project("SUSE:Maintenance", requests)
        self.assertEqual(len(requests), 0)

    def test_assigned_roles_request(self):
        request = Request.parse(self.remote, self.req_assign)[0]
        assigned = request.assigned_roles
        self.assertEqual(len(assigned), 1)
        self.assertEqual(assigned[0].user, 'anonymous')
        self.assertEqual(assigned[0].group, 'qam-sle')

    def test_unassigned_removes_roles(self):
        request = Request.parse(self.remote, self.req_unassign)[0]
        assigned = request.assigned_roles
        self.assertEqual(len(assigned), 0)

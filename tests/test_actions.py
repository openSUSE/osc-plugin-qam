import mock
import os
import unittest
from osc.core import Request
from oscqam import actions, models


path = os.path.join(os.path.dirname(__file__), 'data')


def read_path(path):
    return open(path).read()


class MockRemote(object):
    def get(self, *args, **kwargs):
        pass

    def post(self, *args, **kwargs):
        pass


class UndoAction(actions.OscAction):
    def __init__(self):
        # Don't call super to prevent query to model objects.
        self.undo_stack = []
        self.undos = []

    def action(self):
        self.undo_stack.append(lambda: self.undos.append(1))
        raise models.RemoteError(None, None, None, None, None)


class ActionTests(unittest.TestCase):

    def setUp(self):
        self.mock_remote = MockRemote()
        self.group_xml = read_path(os.path.join(path, 'group_1.xml'))
        self.user_group_xml = read_path(os.path.join(path, 'group_user.xml'))
        self.user_xml = read_path(os.path.join(path, 'user_1.xml'))
        self.req_1_xml = read_path(os.path.join(path, 'request_1.xml'))
        self.req_2_xml = read_path(os.path.join(path, 'request_2.xml'))

    def test_undo(self):
        u = UndoAction()
        u()
        self.assertEqual(u.undos, [1])

    @mock.patch('oscqam.actions.User', autospec=True)
    @mock.patch('oscqam.actions.Group', autospec=True)
    def test_infer_groups(self, pgroup, puser):
        puser.by_name.return_value = models.User.parse(self.mock_remote,
                                                       self.user_xml)[0]
        groups_mock = mock.PropertyMock(
            return_value=models.Group.parse_entry(self.mock_remote,
                                                  self.user_group_xml)
        )
        type(puser.by_name.return_value).groups = groups_mock
        pgroup.all.return_value = models.Group.parse(self.mock_remote,
                                                     self.group_xml)
        pgroup.for_name.return_value = models.Group.parse(self.mock_remote,
                                                          self.group_xml)[0]
        actions.Request.by_id = mock.Mock(
            return_value=models.Request.parse(self.mock_remote,
                                              self.req_1_xml)[0]

        )
        actions.Request.review_assign = mock.Mock()
        assign_action = actions.AssignAction(self.mock_remote, 'anonymous',
                                             '123456')
        assign_action()
        actions.Request.review_assign.assert_called_once()

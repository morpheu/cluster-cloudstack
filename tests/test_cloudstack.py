import unittest
import os
from mock import patch
from cluster_cloudstack.cloudstack import CloudStack, CloudMonkeyRegionError
from utils import FakeURLopenResponse


class TestCloudStack(unittest.TestCase):

    def setUp(self):
        self.urlopen_patcher = patch('urllib2.urlopen')
        self.urlopen_mock = self.urlopen_patcher.start()
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
        self.cloudmonkey_file = open(os.path.join(self.fixtures_dir, 'cloudmonkey_config'), 'r')
        self.virtualmachines_file = open(os.path.join(self.fixtures_dir, 'virtualmachines.json'), 'r')

    def tearDown(self):
        self.urlopen_patcher.stop()

    @patch('__builtin__.open')
    @patch('os.path.expanduser')
    def test_failed_to_find_cloudmonkey_config(self, os_expand_path, open_mock):
        open_mock.side_effect = IOError("no such file or directory: cloudmonkey_config")
        os_expand_path.return_value = '/user/path/.cloudmonkey/config'
        self.assertRaisesRegexp(OSError, "File /user/path/.cloudmonkey/config was not found",
                                CloudStack, "foobar")

    @patch('__builtin__.open')
    def test_failed_to_find_test_region(self, open_mock):
        open_mock.return_value = self.cloudmonkey_file
        self.assertRaisesRegexp(CloudMonkeyRegionError, "No section: 'test'", CloudStack, "test")

    @patch('__builtin__.open')
    def test_make_request_with_optional_projectid(self, open_mock):
        open_mock.return_value = self.cloudmonkey_file
        response_data = '{"foocallresponse":{}}'
        self.urlopen_mock.return_value = FakeURLopenResponse(response_data)
        cloudstack_handler = CloudStack('lab')
        cloudstack_handler.foocall()
        expected_call = self.urlopen_mock.call_args[0][0]
        self.assertIn("projectid=abcde12345", expected_call)
        self.assertEqual(self.urlopen_mock.call_count, 1)

    @patch('__builtin__.open')
    def test_get_all_machine_data(self, open_mock):
        open_mock.return_value = self.cloudmonkey_file
        response_data = self.virtualmachines_file.read()
        self.urlopen_mock.return_value = FakeURLopenResponse(response_data)
        cloudstack_handler = CloudStack('foobar')
        machine_data = cloudstack_handler.get_machines_data()
        expected_response_data = [{'zonename': u'red', 'ipaddress': u'10.2.3.2', 'name': u'test1',
                                   'id': u'123'},
                                  {'zonename': u'blue', 'ipaddress': u'10.1.2.2', 'name': u'test2',
                                   'id': u'456'},
                                  {'zonename': u'blue', 'ipaddress': u'10.1.2.3', 'name': u'test2',
                                   'id': u'987'},
                                  {'zonename': u'red', 'ipaddress': u'10.2.3.4', 'name': u'test3',
                                   'id': u'789'}]
        self.assertEqual(machine_data, expected_response_data)

    @patch('__builtin__.open')
    def test_get_only_red_zone_on_machine_data(self, open_mock):
        open_mock.return_value = self.cloudmonkey_file
        response_data = self.virtualmachines_file.read()
        self.urlopen_mock.return_value = FakeURLopenResponse(response_data)
        cloudstack_handler = CloudStack('foobar')
        machine_data = cloudstack_handler.get_machines_data("red")
        expected_response_data = [{'zonename': u'red', 'ipaddress': u'10.2.3.2', 'name': u'test1',
                                   'id': u'123'},
                                  {'zonename': u'red', 'ipaddress': u'10.2.3.4', 'name': u'test3',
                                   'id': u'789'}]
        self.assertEqual(machine_data, expected_response_data)

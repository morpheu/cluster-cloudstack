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
        self.open_patcher = patch('__builtin__.open')
        self.open_mock = self.open_patcher.start()

    def tearDown(self):
        self.urlopen_patcher.stop()
        self.open_patcher.stop()

    @patch('os.path.expanduser')
    def test_failed_to_find_cloudmonkey_config(self, os_expand_path):
        self.open_mock.side_effect = IOError("no such file or directory: cloudmonkey_config")
        os_expand_path.return_value = '/user/path/.cloudmonkey/config'
        self.assertRaisesRegexp(OSError, "File /user/path/.cloudmonkey/config was not found",
                                CloudStack, "foobar")

    def test_failed_to_find_test_region(self):
        self.open_mock.return_value = self.cloudmonkey_file
        self.assertRaisesRegexp(CloudMonkeyRegionError, "No section: 'test'", CloudStack, "test")

    def test_get_all_machine_data(self):
        self.open_mock.return_value = self.cloudmonkey_file
        response_data = '{"listvirtualmachines":[{"displayname": "test1", "id": "123", "nic":[{"ipaddress":"10.2.3.2"}], "zonename":"red"}]}'
        self.urlopen_mock.return_value = FakeURLopenResponse(response_data)
        cloudstack_handler = CloudStack('foobar')
        machine_data = cloudstack_handler.get_machines_data()
        self.assertEqual(machine_data, {'name': 'test1', 'id': '123', 'ipaddress': '10.2.3.2', 'zonename': 'red'})

import unittest
import os
from mock import patch
from cluster_cloudstack.cloudstack import CloudStack, CloudMonkeyRegionError


class TestCloudStack(unittest.TestCase):

    def setUp(self):
        self.urlopen_patcher = patch('urllib2.urlopen')
        self.urlopen_mock = self.urlopen_patcher.start()
        self.cloudmonkey_config = os.path.join(os.path.dirname(__file__), 'fixtures/cloudmonkey_config')
        self.cloudmonkey_open_file = open(self.cloudmonkey_config, 'r')
        self.open_patcher = patch('__builtin__.open')
        self.open_mock = self.open_patcher.start()

    def tearDown(self):
        self.urlopen_patcher.stop()
        self.open_patcher.stop()
        pass

    @patch('os.path.expanduser')
    def test_failed_to_find_cloudmonkey_config(self, os_expand_path):
        self.open_mock.side_effect = IOError("no such file or directory: {}".format(self.cloudmonkey_config))
        os_expand_path.return_value = '/user/path/.cloudmonkey/config'
        self.assertRaisesRegexp(OSError, "File /user/path/.cloudmonkey/config was not found",
                                CloudStack, "foobar")

    def test_failed_to_find_test_region(self):
        self.open_mock.return_value = self.cloudmonkey_open_file
        self.assertRaisesRegexp(CloudMonkeyRegionError, "No section: 'test'", CloudStack, "test")

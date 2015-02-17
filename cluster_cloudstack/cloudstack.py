# -*- coding: utf-8 -*-

from connector import CloudStackRequester
from ConfigParser import RawConfigParser, NoSectionError
import os


class CloudMonkeyRegionError(Exception):

    def __init__(self, msg):
        super(Exception, self).__init__(msg)
        self.msg = msg

    def __str__(self):
        return self.msg

    def __unicode__(self):
        return unicode(str(self))


class CloudStack(CloudStackRequester):

    def __init__(self, region):
        try:
            # import keys from cloudmonkey config
            parser = RawConfigParser()
            cloudmonkey_config = os.path.expanduser('~/.cloudmonkey/config')
            parsed_config = parser.read(cloudmonkey_config)
            if len(parsed_config) == 0:
                raise OSError("File {} was not found".format(cloudmonkey_config))
            self.apikey = parser.get(region, 'apikey')
            self.api_url = parser.get(region, 'url')
            self.secretkey = parser.get(region, 'secretkey')
        except NoSectionError, e:
            raise CloudMonkeyRegionError(e.message)
        except OSError, e:
            raise e
        except Exception, e:
            raise e

        super(CloudStack, self).__init__(self.apikey, self.api_url, self.secretkey)

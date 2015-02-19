# -*- coding: utf-8 -*-

from io import StringIO


class FakeURLopenResponse(StringIO):

    def __init__(self, *args):
        try:
            self.code = args[1]
        except IndexError:
            self.code = 200
            pass
        try:
            self.msg = args[2]
        except IndexError:
            self.msg = "OK"
            pass
        self.headers = {'content-type': 'text/plain; charset=utf-8'}
        StringIO.__init__(self, unicode(args[0]))

    def getcode(self):
        return self.code


class DataStorage(StringIO):

    last_read_data = None

    def __init__(self, *args):
        try:
            StringIO.__init__(self, unicode(args[0]))
        except:
            StringIO.__init__(self, unicode(DataStorage.last_read_data))

    def close(self):
        self.seek(0)
        DataStorage.last_read_data = self.read()
        StringIO.close(self)

    def write(self, data):
        StringIO.write(self, unicode(data))

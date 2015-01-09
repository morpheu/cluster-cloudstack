#!/usr/bin/env python

from cloudmonkey.config import config_file, read_config, config_fields
from cloudmonkey.requester import monkeyrequest
import os
import sys
import logging
import argparse
logger = logging.getLogger(__name__)

class CommandNotFoundError(Exception):

    def __init__(self, name):
        super(Exception, self).__init__(name)
        self.name = name

    def __str__(self):
        return """command "{}" not found""".format(self.name)

    def __unicode__(self):
        return unicode(str(self))

class CloudStackRequester(object):

    def __init__(self, cfile):
        self.config_file = cfile
        self.config_options = read_config(self.get_attr, self.set_attr,
                                          self.config_file)

    def get_attr(self, field):
        return getattr(self, field)

    def set_attr(self, field, value):
        return setattr(self, field, value)  

    def make_request(self, command, args={}, isasync=False):
        if self.projectid is not None:
            args['projectid'] =  self.projectid
        response, error = monkeyrequest(command, args, isasync,
                                        self.asyncblock, logger,
                                        self.host, self.port,
                                        self.apikey, self.secretkey,
                                        self.timeout, self.protocol, self.path)
        if error is not None:
            sys.stderr.write(error + '\n')
            sys.exit(1)
        return response


config_fields['user']['projectid'] = ''
cloudstack_request = CloudStackRequester(config_file)
virtual_machines = cloudstack_request.make_request('listVirtualMachines')

def _get_machines_ips(machine_name=None):
    machines = {}
    if not 'virtualmachine' in virtual_machines['listvirtualmachinesresponse']:
        sys.stderr.write('Empty virtual machines list. Maybe wrong or empty projectid? \n')
        return machines
    for machine in virtual_machines['listvirtualmachinesresponse']['virtualmachine']:
        if not machine['displayname'] in machines:
            machines[machine['displayname']] = []
        machines[machine['displayname']].append(machine['nic'][0]['ipaddress'])
    if machine_name in machines:
        return machines[machine_name]
    return machines

def list_machines(args):
    machines = _get_machines_ips()
    for (machine, ips) in sorted(machines.items()):
        print machine

def get_ips(args):
    if len(args) == 0:
        sys.stderr.write(__file__ + " get-ips <machine_name> [-o]\n")
        sys.stderr.write("Missing machine name\n")
        sys.exit(2)
    ips = _get_machines_ips(args[0])
    if type(ips) is dict:
        sys.stderr.write("Machine not found\n")
        sys.exit(1)
    if '-o' in args:
        print ips[0]
        sys.exit(0)
    print ' '.join(ips)

def available_commands():
    return {
        "list-machines": list_machines,
        "get-ips": get_ips,
    }

def get_command(name):
    command = available_commands().get(name)
    if not command:
        raise CommandNotFoundError(name)
    return command


def help_commands():
    sys.stderr.write('Available commands:\n')
    for key in available_commands().keys():
        sys.stderr.write(' {}\n'.format(key))


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    if len(args) == 0:
        help_commands()
        return
    cmd, args = args[0], args[1:]
    try: 
        command = get_command(cmd)
        command(args)
    except CommandNotFoundError as e:
        help_commands()
        sys.stderr.write(unicode(e) + u"\n")
        sys.exit(2)

if __name__ == "__main__":
    main()

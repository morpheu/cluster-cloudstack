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

def _get_machines_ips(machine_name=None):
    global cloudstack_request
    machines = {}
    virtual_machines = cloudstack_request.make_request('listVirtualMachines')
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

def _list_networks(network_name=None):
    virtual_networks = cloudstack_request.make_request('listNetworks')
    networks = {}
    if not 'network' in virtual_networks['listnetworksresponse']:
        sys.stderr.write('Empty networks list. Maybe wrong or empty projectid? \n')
        return networks
    for network in virtual_networks['listnetworksresponse']['network']:
        name = network['name']
        networks[name] = {'cidr': network['cidr'], 'id': network['id'], 'zoneid': network['zoneid']}
    if network_name is not None:
        return [{network:networks[network]} for network in networks.keys() if network_name.lower() in network.lower()]
    return networks

def list_machines(args):
    machines = _get_machines_ips()
    for (machine, ips) in sorted(machines.items()):
        print machine

def list_networks(args):
    networks = _list_networks()
    for name in sorted(networks):
        print "{:50s} {}".format(name, networks[name]['cidr'])

def network_info(args):
    if len(args) == 0:
        sys.stderr.write(__file__ + " network_info <network_name>\n")
        sys.stderr.write("Missing network name\n")
        sys.exit(2)
    network_name = args[0]
    networks = _list_networks(network_name)
    print "{:50s} {:18s} {:36s} {:36s}".format("Network Name", "CIDR", "Network ID", "Zone ID")
    for network in sorted(networks):
        network_name = network.keys()[0]
        print "{:50s} {:18s} {:36s} {:36s}".format(network_name, network[network_name]['cidr'],
                                                   network[network_name]['id'],
                                                   network[network_name]['zoneid'])


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
        "list-networks": list_networks,
        "get-machines-ips": get_ips,
        "get-network-info": network_info
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

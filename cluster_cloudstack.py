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
    global cloudstack_request
    virtual_networks = cloudstack_request.make_request('listNetworks')
    networks = []
    if not 'network' in virtual_networks['listnetworksresponse']:
        sys.stderr.write('Empty networks list. Maybe wrong or empty projectid? \n')
        return networks
    for network in virtual_networks['listnetworksresponse']['network']:
        networks.append({'name': network['name'], 'cidr': network['cidr'], 'id': network['id'],
                         'zoneid': network['zoneid'], 'zonename': network['zonename']})
    if network_name is not None:
        return [network for network in networks if network_name.lower() in network['name'].lower()]
    return networks

def _list_os_templates(template_name=None):
    global cloudstack_request
    machine_templates = cloudstack_request.make_request('listTemplates', {'templatefilter': 'self'})
    templates = []
    if not 'template' in machine_templates['listtemplatesresponse']:
        sys.stderr.write('Empty templates list. Maybe wrong or empty projectid? \n')
        return templates
    for template in machine_templates['listtemplatesresponse']['template']:
        templates.append({'name': template['name'], 'displaytext': template['displaytext'],
                          'zoneid': template['zoneid'], 'id': template['id'],
                          'ostypename': template['ostypename'], 'zonename': template['zonename']})
    if template_name is not None:
        return [template for template in templates if template_name.lower() in template['name'].lower()]
    return templates

def _list_service_offering(offering_name=None):
    global cloudstack_request
    vm_offerings = cloudstack_request.make_request('listServiceOfferings')
    service_offerings = []
    if not 'serviceoffering' in vm_offerings['listserviceofferingsresponse']:
        sys.stderr.write('Empty service offering list. Maybe wrong or empry projectid? \n')
        return service_offerings
    for vm in vm_offerings['listserviceofferingsresponse']['serviceoffering']:
        service_offerings.append({'name': vm['name'], 'displaytext': vm['displaytext'], 'id': vm['id']})
    if offering_name is not None:
        return [offering for offering in service_offerings if offering_name.lower() in offering['name'].lower()]
    return service_offerings

def list_machines(args):
    machines = _get_machines_ips()
    for (machine, ips) in sorted(machines.items()):
        print machine

def list_networks(args):
    networks = _list_networks()
    for network in sorted(networks, key=lambda k: k['name']):
        print "{:50s} {}".format(network['name'], network['cidr'])

def list_os_templates(args):
    templates = _list_os_templates()
    print "{:35s} {:35s} {:36s} {:36s}".format("Template Description", "OS Type", "Template ID", "Zone Name")
    for template in sorted(templates, key=lambda k: k['displaytext']):
        print "{:35s} {:35s} {:36s} {:36s}".format(template['displaytext'], template['ostypename'],
                                                   template['id'], template['zonename'])

def template_info(args):
    if len(args) == 0:
        sys.stderr.write(__file__ + " template_info <template_name>\n")
        sys.stderr.write("Missing network name\n")
        sys.exit(2) 

def network_info(args):
    if len(args) == 0:
        sys.stderr.write(__file__ + " network_info <network_name>\n")
        sys.stderr.write("Missing network name\n")
        sys.exit(2)
    network_name = args[0]
    networks = _list_networks(network_name)
    print "{:50s} {:18s} {:36s} {:36s}".format("Network Name", "CIDR", "Network ID", "Zone Name")
    for network in sorted(networks, key=lambda k: k['name']):
        print "{:50s} {:18s} {:36s} {:36s}".format(network['name'], network['cidr'],
                                                   network['id'], network['zonename'])

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

def generate_template_parser(args):
    parser = argparse.ArgumentParser("generate-template")
    parser.add_argument("template", nargs=1, help="Template name")
    parser.add_argument("-t", "--os_template_id", required=True, help="OS Template id")
    parser.add_argument("-n", "--network_name", required=True, help="Network name prefix")
    parser.add_argument("-o", "--service_offering", required=True, help="Service offering machine name")
    parser.add_argument("-d", "--disk_offering_id", default=None, required=False, help="Disk offering id")
    parser.add_argument("-s", "--disk_offering_size", default=None, required=False, help="Disk offering size - for custom disk size")
    parsed = parser.parse_args(args)
    return parsed

def generate_template(args):
    global cloudstack_request
    args = generate_template_parser(args)
    template_name = args.template[0]
    os_template_id = args.os_template_id
    networks = _list_networks(args.network_name)
    service_offering = _list_service_offering(args.service_offering)[0]
    project_id = cloudstack_request.get_attr('projectid')
    disk_offering_id = args.disk_offering_id
    disk_offering_size = args.disk_offering_size
    for network in networks:
        template_line = "projectid={} displayname={} networkids={} templateid={} \
                         serviceofferingid={} zoneid={}".format(project_id, template_name, network['id'],
                                                                os_template_id, service_offering['id'],
                                                                network['zoneid'])
        if disk_offering_id is not None:
            template_line += " diskofferingid={}".format(disk_offering_id)
        if disk_offering_size is not None:
            template_line += " size={}".format(disk_offering_size)
        print template_line

def available_commands():
    return {
        "list-machines": list_machines,
        "list-networks": list_networks,
        "list-os-templates": list_os_templates,
        "get-machines-ips": get_ips,
        "get-network-info": network_info,
        "generate-template": generate_template
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

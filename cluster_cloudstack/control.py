# -*- coding: utf-8 -*-

import sys
import argparse
import base64


class CommandNotFoundError(Exception):

    def __init__(self, name):
        super(Exception, self).__init__(name)
        self.name = name

    def __str__(self):
        return """command "{}" not found""".format(self.name)

    def __unicode__(self):
        return unicode(str(self))


def list_machines(args):
    machines = _get_machines_data()
    for machine_name in sorted(set([machine['name'] for machine in machines])):
        print machine_name

def get_machine_info(args):
    if len(args) == 0:
        sys.stderr.write(__file__ + " machine-info <display_name|ipaddress|zonename|vm id>\n")
        sys.stderr.write("Missing required search term\n")
        sys.exit(2)
    search_item = args[0]
    machines = _get_machines_data(search_item)
    print "{:50s} {:18s} {:36s} {:36s}".format("Display Name", "IP Address", "VM ID", "Zone Name")
    for machine in sorted(machines, key=lambda k: k['zonename']):
        print "{:50s} {:18s} {:36s} {:36s}".format(machine['name'], machine['ipaddress'],
                                                   machine['id'], machine['zonename'])

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

def list_service_offerings(args):
    service_offering = _list_service_offering()
    print "{:25s} {:30s} {:30s}".format("Offering Name", "Description", "Id")
    for offering in sorted(service_offering, key=lambda k: k['name']):
        print "{:25s} {:30s} {:30s}".format(offering['name'], offering['displaytext'], offering['id'])

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
    machine_data = _get_machines_data(args[0])
    ips = [machine['ipaddress'] for machine in machine_data if machine['name'] == args[0]]
    if ips == []:
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
        template_line = """
{} projectid={} displayname={} networkids={} templateid={} serviceofferingid={} zoneid={}"""
        template_line = template_line.format(network['zonename'], project_id, template_name, network['id'],
                                             os_template_id, service_offering['id'],
                                             network['zoneid'])
        if disk_offering_id is not None:
            template_line += " diskofferingid={}".format(disk_offering_id)
        if disk_offering_size is not None:
            template_line += " size={}".format(disk_offering_size)
        print template_line

def update_machine_parser(args):
    parser = argparse.ArgumentParser("update-machine")
    parser.add_argument("-i", "--machine_id", default=None, required=False, help="Only update this machine id")
    parser.add_argument("-m", "--machine_name", required=True, help="Machine display name")
    parser.add_argument("-f", "--user_data_file", required=True, help="User data file")
    parser.add_argument("-d", "--dry_run", required=False, action='store_true', help="Dry run mode")
    parsed = parser.parse_args(args)
    return parsed

def b64_encoded(file_path):
    with open (file_path, "r") as f:
        data=f.read()
        f.close
    encoded_file = base64.b64encode(data)
    return encoded_file

def _update_machine_userdata(machine_id, user_data):
    global cloudstack_request
    updated_machine = cloudstack_request.make_request('updateVirtualMachine', 
                                                        {'id': machine_id, 'userdata': user_data})
    if machine_id in updated_machine['updatevirtualmachineresponse']['virtualmachine']['id']:
        machine_display_name = updated_machine['updatevirtualmachineresponse']['virtualmachine']['displayname']
        print "Userdata for virtual machine {} with {} ID updated".format(machine_display_name, machine_id)

def update_machine_userdata(args):
    args = update_machine_parser(args)
    machine_data = _get_machines_data(args.machine_name)
    if machine_data == []:
        sys.stderr.write("Machine {} not found\n".format(args.machine_name))
        sys.exit(1)
    encoded_user_data = b64_encoded(args.user_data_file)
    changed_user_data = False
    for machine_id in [machine['id'] for machine in machine_data]:
        if args.machine_id is not None and machine_id != args.machine_id:
            continue
        changed_user_data = True
        print "Update userdata on {} with id {}".format(args.machine_name, machine_id)
        if not args.dry_run:
            _update_machine_userdata(machine_id, encoded_user_data)
    if not changed_user_data:
        print "No machine found for {} id on {}".format(args.machine_id, args.machine_name)

def available_commands():
    return {
        "list-machines": list_machines,
        "list-networks": list_networks,
        "list-os-templates": list_os_templates,
        "list-service-offerings": list_service_offerings,
        "get-machines-ips": get_ips,
        "get-network-info": network_info,
        "get-machine-info": get_machine_info,
        "generate-template": generate_template,
        "update-machine-userdata": update_machine_userdata
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

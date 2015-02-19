# -*- coding: utf-8 -*-

from connector import CloudStackRequester
from ConfigParser import RawConfigParser, NoSectionError, NoOptionError
import os
import sys


class CloudMonkeyRegionError(Exception):

    def __init__(self, msg):
        super(Exception, self).__init__(msg)
        self.msg = msg

    def __str__(self):
        return self.msg

    def __unicode__(self):
        return unicode(str(self))


class CloudStack(CloudStackRequester):

    def __init__(self, region=None, **kwargs):
        try:
            # import keys from cloudmonkey config
            parser = RawConfigParser()
            cloudmonkey_config = os.path.expanduser('~/.cloudmonkey/config')
            parsed_config = parser.read(cloudmonkey_config)
            if len(parsed_config) == 0:
                raise OSError("File {} was not found".format(cloudmonkey_config))
            if region is None:
                region = parser.get('default_region', 'region')
            self.apikey = parser.get(region, 'apikey')
            self.api_url = parser.get(region, 'url')
            self.secretkey = parser.get(region, 'secretkey')
            self.projectid = parser.get(region, 'projectid')
        except NoSectionError, e:
            raise CloudMonkeyRegionError(e.message)
        except NoOptionError, e:
            if "projectid" in e.message:
                self.projectid = None
            else:
                raise e
        except Exception, e:
            raise e

        super(CloudStack, self).__init__(self.apikey, self.api_url, self.secretkey, self.projectid)

        if 'set_default_region' in kwargs:
            self.set_config_section('default_region', region=region)

        if 'project_name' in kwargs:
            self.projectid = self.get_project_id(kwargs['project_name'])
            if 'set_project_id' in kwargs and self.projectid is not None:
                self.set_config_section(region, projectid=self.projectid)

    def set_config_section(self, section, **kwargs):
        try:
            parser = RawConfigParser()
            cloudmonkey_config = os.path.expanduser('~/.cloudmonkey/config')
            parsed_config = parser.read(cloudmonkey_config)
            if len(parsed_config) == 0:
                raise OSError("File {} was not found".format(cloudmonkey_config))
            if not parser.has_section(section):
                parser.add_section(section)
            for key in kwargs.keys():
                parser.set(section, key, kwargs[key])
            with open(cloudmonkey_config, 'wb') as configfile:
                parser.write(configfile)
        except Exception, e:
            raise e

    def get_project_id(self, project_name):
        projects = self.listProjects()
        if 'project' not in projects:
            return None
        for project in projects['project']:
            if project['name'].lower() == project_name.lower():
                return project['id']
        return None

    def get_machines_data(self, search_item=None):
        machines = []
        virtual_machines = self.listVirtualMachines()
        search_result = []
        if 'virtualmachine' not in virtual_machines:
            sys.stderr.write('Empty virtual machines list. Maybe wrong or empty projectid? \n')
            return machines
        for machine in virtual_machines['virtualmachine']:
            machine_data = {'name': machine['displayname'], 'id': machine['id'],
                            'ipaddress': machine['nic'][0]['ipaddress'], 'zonename': machine['zonename']}
            machines.append(machine_data)
            if search_item in [item for item in machine_data.values()]:
                search_result.append(machine_data)
        if search_result != [] or search_item is not None:
            return search_result
        return machines

    def list_networks(self, network_name=None):
        virtual_networks = self.listNetworks()
        networks = []
        if 'network' not in virtual_networks['listnetworksresponse']:
            sys.stderr.write('Empty networks list. Maybe wrong or empty projectid? \n')
            return networks
        for network in virtual_networks['listnetworksresponse']['network']:
            networks.append({'name': network['name'], 'cidr': network['cidr'], 'id': network['id'],
                            'zoneid': network['zoneid'], 'zonename': network['zonename']})
        if network_name is not None:
            return [network for network in networks if network_name.lower() in network['name'].lower()]
        return networks

    def list_os_templates(self, template_name=None):
        machine_templates = self.listTemplates({'templatefilter': 'self'})
        templates = []
        if 'template' not in machine_templates['listtemplatesresponse']:
            sys.stderr.write('Empty templates list. Maybe wrong or empty projectid? \n')
            return templates
        for template in machine_templates['listtemplatesresponse']['template']:
            templates.append({'name': template['name'], 'displaytext': template['displaytext'],
                              'zoneid': template['zoneid'], 'id': template['id'],
                              'ostypename': template['ostypename'], 'zonename': template['zonename']})
        if template_name is not None:
            return [template for template in templates if template_name.lower() in template['name'].lower()]
        return templates

    def list_service_offering(self, offering_name=None):
        vm_offerings = self.listServiceOfferings()
        service_offerings = []
        if 'serviceoffering' not in vm_offerings['listserviceofferingsresponse']:
            sys.stderr.write('Empty service offering list. Maybe wrong or empry projectid? \n')
            return service_offerings
        for vm in vm_offerings['listserviceofferingsresponse']['serviceoffering']:
            service_offerings.append({'name': vm['name'], 'displaytext': vm['displaytext'], 'id': vm['id']})
        if offering_name is not None:
            return [offering for offering in service_offerings if offering_name.lower() in offering['name'].lower()]
        return service_offerings

#! /usr/bin/python
#
# (c) 2017, Drew Bomhof <dbomhof@redhat.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import (absolute_import, division, print_function)
import os

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: manageiq_automate
'''
import dpath.util
from ansible.module_utils.basic import AnsibleModule


try:
    from manageiq_client.api import ManageIQClient
    HAS_CLIENT = True
except ImportError:
    HAS_CLIENT = False


def check_client(module):
    if not HAS_CLIENT:
        module.fail_json(msg='manageiq_client.api is required for this module')


def validate_connection_params(module):
    params = module.params['manageiq_connection']
    error_str = "missing required argument: manageiq_connection[{}]"
    url = params['url']
    token = params.get('token')
    username = params.get('username')
    password = params.get('password')

    if (url and username and password) or (url and token):
        return params
    for arg in ['url', 'username', 'password']:
        if params[arg] in (None, ''):
            module.fail_json(msg=error_str.format(arg))


class ManageIQ(object):
    """
        class encapsulating ManageIQ API client.
    """

    def __init__(self, module):
        # handle import errors
        check_client(module)
        params = validate_connection_params(module)

        url = params['url']
        username = params.get('username')
        password = params.get('password')
        token = params.get('token')
        verify_ssl = params.get('verify_ssl')
        ca_bundle_path = params.get('ca_bundle_path')

        self._module = module
        self._api_url = url + '/api'
        self._auth = dict(user=username, password=password, token=token)
        try:
            self._client = ManageIQClient(self._api_url, self._auth, verify_ssl=verify_ssl, ca_bundle_path=ca_bundle_path)
        except Exception as e:
            self.module.fail_json(msg="failed to open connection (%s): %s" % (url, str(e)))

    @property
    def module(self):
        """ Ansible module module

        Returns:
            the ansible module
        """
        return self._module

    @property
    def api_url(self):
        """ Base ManageIQ API

        Returns:
            the base ManageIQ API
        """
        return self._api_url

    @property
    def client(self):
        """ ManageIQ client

        Returns:
            the ManageIQ client
        """
        return self._client


class ManageIQAutomate(object):
    """
        Object to execute automate workspace management operations in manageiq.
    """

    def __init__(self, manageiq, workspace):
        self._manageiq = manageiq
        self._target = workspace

        self._module = self._manageiq.module
        self._api_url = self._manageiq.api_url
        self._client = self._manageiq.client
        self._error = None


    def url(self):
        """
            The url to connect to the workspace
        """
        url_str = self._manageiq.module.params['manageiq_connection']['automate_workspace']
        return self._api_url + '/' + url_str


    def href_slug_url(self, value):
        """
            The url to connect to the vmdb
        """
        base_url = value.split('::')[1]
        return self._api_url + '/' + base_url


    def get(self, alt_url=None):
        """
            Get any attribute, object from the REST API
        """
        if alt_url:
            url = alt_url
        else:
            url = self.url()
        result = self._client.get(url)
        return dict(result=result)


    def set(self, data):
        """
            Set any attribute, object from the REST API
        """
        result = self._client.post(self.url(), action='edit', resource=data)
        return  result


    def exists(self, path):
        """
            Validate all passed objects before attempting to set or get values from them
        """

        try:
            return bool(dpath.util.get(self._target, path, '|'))
        except KeyError as error:
            return False


    def auto_commit(self):
        """ ManageIQAutomate

        Returns:
            Boolean auto_commit on or off
        """
        return bool(self._target['workspace']['options'].get('auto_commit'))


class Workspace(ManageIQAutomate):
    """
        Object to modify and get the Workspace
    """

    def set_or_commit(self):
        """
            Commit the workspace or return the current version
        """
        if self.auto_commit():
            return self.commit_workspace()
        return dict(changed=True, workspace=self._target['workspace'])


    def object_exists(self, dict_options):
        """
            Check if the specific object exists
        """

        search_path = "workspace|result|input|objects|" + dict_options['object']
        if self.exists(search_path):
            return dict(changed=False, value=True)
        return dict(changed=False, value=False)


    def attribute_exists(self, dict_options):
        """
            Check if the specific attribute exists
        """

        obj = dict_options['object']
        attribute = dict_options['attribute']
        path = "workspace|result|input|objects"
        search_path = "|".join([path, obj, attribute])
        if self.exists(search_path):
            return dict(changed=False, value=True)
        return dict(changed=False, value=False)


    def state_var_exists(self, dict_options):
        """
            Check if the specific state_var exists
        """

        attribute = dict_options['attribute']
        path = "workspace|result|input|state_vars"
        search_path = "|".join([path, attribute])
        if self.exists(search_path):
            return dict(changed=False, value=True)
        return dict(changed=False, value=False)


    def method_parameter_exists(self, dict_options):
        """
            Check if the specific method_parameter exists
        """

        parameter = dict_options['parameter']
        path = "workspace|result|input|method_parameters"
        search_path = "|".join([path, parameter])
        if self.exists(search_path):
            return dict(changed=False, value=True)
        return dict(changed=False, value=False)


    def get_attribute(self, dict_options):
        """
            Get the passed in attribute from the Workspace
        """

        if self.attribute_exists(dict_options):
            return_value = self._target['workspace']['result']['input']['objects'][dict_options['object']][dict_options['attribute']]

            return dict(changed=False, value=return_value)
        else:
            self._module.fail_json(msg='Object %s Attribute %s does not exist' % (dict_options['object'], dict_options['attribute']))


    def get_state_var(self, dict_options):
        """
            Get the passed in state_var from the Workspace
        """
        return_value = None

        if self.state_var_exists(dict_options):
            return_value = self._target['workspace']['result']['input']['state_vars'][dict_options['attribute']]

            return dict(changed=False, value=return_value)
        else:
            self._module.fail_json(msg='State Var %s does not exist' % dict_options['attribute'])


    def get_method_parameter(self, dict_options):
        """
            Get the passed in method_parameter from the Workspace
        """
        return_value = None

        if self.method_parameter_exists(dict_options):
            return_value = self._target['workspace']['result']['input']['method_parameters'][dict_options['parameter']]

            return dict(changed=False, value=return_value)
        else:
            self._module.fail_json(msg='Method Parameter %s does not exist' % dict_options['parameter'])


    def get_object_names(self):
        """
            Get a list of all current object names
        """

        return_value = self._target['workspace']['result']['input']['objects'].keys()
        return dict(changed=False, value=return_value)


    def get_method_parameters(self):
        """
            Get a list of all current method_paramters
        """

        return_value = self._target['workspace']['result']['input']['method_parameters']
        return dict(changed=False, value=return_value)


    def get_state_var_names(self):
        """
            Get a list of all current state_var names
        """

        return_value = self._target['workspace']['result']['input']['state_vars'].keys()
        return dict(changed=False, value=return_value)


    def get_object_attribute_names(self, dict_options):
        """
            Get a list of all object_attribute names
        """

        if self.object_exists(dict_options):
            return_value = self._target['workspace']['result']['input']['objects'][dict_options['object']].keys()
            return dict(changed=False, value=return_value)
        else:
            self._module.fail_json(msg='Object %s does not exist' % dict_options['object'])


    def get_vmdb_object(self, dict_options):
        """
            Get a vmdb object via an href_slug passed in on an attribute
        """
        result = self.get_attribute(dict_options)
        attribute = dict_options['attribute']
        obj = dict_options['object']
        if self.object_exists(dict_options):
            vmdb_object = self.get(self.href_slug_url(result['value']))
            return dict(changed=False, value=vmdb_object['result'])
        else:
            self._module.fail_json(msg='Attribute %s does not exist for Object %s' % (attribute, obj))


    def set_state_var(self, dict_options):
        """
            Set the state_var called with the passed in value
        """

        new_attribute = dict_options['attribute']
        new_value = dict_options['value']
        self._target['workspace']['result']['input']['state_vars'][new_attribute] = new_value
        self._target['workspace']['result']['output']['state_vars'][new_attribute] = new_value
        return self.set_or_commit()


    def set_retry(self, dict_options):
        """
            Set Retry
        """
        attributes = dict()
        attributes['object'] = 'root'
        attributes['attributes'] = dict(ae_result='retry', ae_retry_limit=dict_options['interval'])

        self.set_attributes(attributes)
        return self.set_or_commit()


    def set_attribute(self, dict_options):
        """
            Set the attribute called on the object with the passed in value
        """

        new_attribute = dict_options['attribute']
        new_value = dict_options['value']
        obj = dict_options['object']
        if self.object_exists(dict_options):
            self._target['workspace']['result']['input']['objects'][obj][new_attribute] = new_value
            new_dict = {obj:{new_attribute: new_value}}
            self._target['workspace']['result']['output']['objects'] = new_dict
            return self.set_or_commit()
        else:
            msg = 'Failed to set the attribute %s with value %s for %s' % (new_attribute, new_value, obj)
            self._module.fail_json(msg=msg, changed=False)


    def set_attributes(self, dict_options):
        """
            Set the attributes called on the object with the passed in values
        """
        new_attributes = dict_options['attributes']

        obj = dict_options['object']
        if self.object_exists(dict_options):
            for new_attribute, new_value in new_attributes.iteritems():
                self._target['workspace']['result']['input']['objects'][obj][new_attribute] = new_value
                if self._target['workspace']['result']['output']['objects'].get(obj) is None:
                    self._target['workspace']['result']['output']['objects'][obj] = dict()
                self._target['workspace']['result']['output']['objects'][obj][new_attribute] = new_value
            return self.set_or_commit()
        else:
            msg = 'Failed to set the attributes %s for %s' % (new_attributes, obj)
            self._module.fail_json(msg=msg, changed=False)


    def commit_workspace(self):
        """
            Commit the workspace
        """
        workspace = self.set(self._target['workspace']['result']['output'])
        return dict(changed=True, workspace=workspace)


    def initialize_workspace(self, dict_options):
        """
            Initialize the Workspace with auto_commit set to true or false
        """

        workspace = self.get()
        workspace['options'] = dict(auto_commit=(dict_options.get('auto_commit') or False))
        workspace['result']['output'] = dict()
        workspace['result']['output']['objects'] = dict()
        workspace['result']['output']['state_vars'] = dict()

        return dict(changed=False, workspace=workspace)


def manageiq_argument_spec():
    return dict(
        url=dict(default=os.environ.get('MIQ_URL', None)),
        username=dict(default=os.environ.get('MIQ_USERNAME', None)),
        password=dict(default=os.environ.get('MIQ_PASSWORD', None), no_log=True),
        token=dict(default=os.environ.get('MIQ_TOKEN', None), no_log=True),
        automate_workspace=dict(default=None, type='str', no_log=True),
        group=dict(default=None, type='str'),
        X_MIQ_Group=dict(default=None, type='str'),
        verify_ssl=dict(default=True, type='bool'),
        ca_bundle_path=dict(required=False, default=None),
    )


def main():
    """
        The entry point to the ManageIQ Automate module
    """
    module = AnsibleModule(
            argument_spec=dict(
                manageiq_connection=dict(required=True, type='dict',
                                         options=manageiq_argument_spec()),
                initialize_workspace=dict(required=False, type='dict'),
                commit_workspace=dict(type='bool', default=False),
                set_attribute=dict(required=False, type='dict'),
                set_attributes=dict(required=False, type='dict'),
                object_exists=dict(required=False, type='str'),
                attribute_exists=dict(required=False, type='dict'),
                state_var_exists=dict(required=False, type='dict'),
                method_parameter_exists=dict(required=False, type='dict'),
                commit_attribute=dict(required=False, type='dict'),
                commit_attributes=dict(required=False, type='dict'),
                commit_state_var=dict(required=False, type='dict'),
                get_attribute=dict(required=False, type='dict'),
                get_state_var=dict(required=False, type='dict'),
                get_method_parameter=dict(required=False, type='dict'),
                set_retry=dict(required=False, type='dict'),
                set_state_var=dict(required=False, type='dict'),
                get_vmdb_object=dict(required=False, type='dict'),
                get_object_names=dict(required=False, type='bool'),
                get_state_var_names=dict(required=False, type='bool'),
                get_method_parameters=dict(required=False, type='bool'),
                get_object_attribute_names=dict(required=False, type='dict'),
                workspace=dict(required=False, type='dict')
                ),
            )

    argument_opts = {
        'initialize_workspace':module.params['initialize_workspace'],
        'commit_workspace':module.params['commit_workspace'],
        'get_attribute':module.params['get_attribute'],
        'get_method_parameter':module.params['get_method_parameter'],
        'get_state_var':module.params['get_state_var'],
        'get_object_attribute_names':module.params['get_object_attribute_names'],
        'get_vmdb_object':module.params['get_vmdb_object'],
        'object_exists':module.params['object_exists'],
        'method_parameter_exists':module.params['method_parameter_exists'],
        'attribute_exists':module.params['attribute_exists'],
        'state_var_exists':module.params['state_var_exists'],
        'set_attribute':module.params['set_attribute'],
        'set_attributes':module.params['set_attributes'],
        'set_retry':module.params['set_retry'],
        'set_state_var':module.params['set_state_var']
        }

    boolean_opts = {
        'get_object_names':module.params['get_object_names'],
        'get_method_parameters':module.params['get_method_parameters'],
        'get_state_var_names':module.params['get_state_var_names']
        }

    manageiq = ManageIQ(module)
    workspace = Workspace(manageiq, module.params['workspace'])

    for key, value in boolean_opts.iteritems():
        if value:
            result = getattr(workspace, key)()
            module.exit_json(**result)
    for key, value in argument_opts.iteritems():
        if value:
            result = getattr(workspace, key)(value)
            module.exit_json(**result)


    module.fail_json(msg="No workspace found")


if __name__ == "__main__":
    main()

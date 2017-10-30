# (c) 2017, Drew Bomhof <dbomhof@redhat.com>
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
from ansible.plugins.action import ActionBase
from ansible.utils.vars import merge_hash

MANAGEIQ_ARGS_MAP = {'token': 'api_token',
                     'url': 'api_url',
                     'username': 'username',
                     'password': 'password',
                     'group': 'group',
                     'automate_workspace': 'automate_workspace',
                     'X-MIQ_Group': 'X-MIQ_Group'}
MANAGEIQ_MODULE_VARS = ('username',
                        'password',
                        'url',
                        'token',
                        'group',
                        'automate_workspace',
                        'X-MIQ_Group')


class ActionModule(ActionBase):

    def manageiq_extra_vars(self, module_vars, task_vars):
        if 'manageiq' not in task_vars.keys():
            return module_vars

        verify_ssl = None
        ca_bundle_path = None

        if 'manageiq_connection' not in module_vars.keys() or module_vars['manageiq_connection'] is None:
            module_vars['manageiq_connection'] = dict()
        if 'verify_ssl' in module_vars['manageiq_connection'].keys():
            verify_ssl = module_vars['manageiq_connection'].pop('verify_ssl', None)
        if 'ca_bundle_path' in module_vars['manageiq_connection'].keys():
            ca_bundle_path = module_vars['manageiq_connection'].pop('ca_bundle_path', None)

        for k in MANAGEIQ_MODULE_VARS:
            if k not in module_vars['manageiq_connection']:
                try:
                    module_vars['manageiq_connection'][k] = task_vars['manageiq'][MANAGEIQ_ARGS_MAP[k]]
                except KeyError:
                    pass

        module_vars['manageiq_connection']['verify_ssl'] = verify_ssl
        module_vars['manageiq_connection']['ca_bundle_path'] = ca_bundle_path

        return module_vars


    def run(self, tmp=None, task_vars=None):
        results = super(ActionModule, self).run(tmp, task_vars or dict())

        module_vars = self.manageiq_extra_vars(self._task.args.copy(), task_vars)

        results = merge_hash(
            results,
            self._execute_module(module_args=module_vars, task_vars=task_vars),
        )

        return results

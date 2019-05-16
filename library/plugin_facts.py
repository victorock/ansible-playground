#
# coding: utf-8 -*-
# (c) 2019, Victor da Costa <victorockeiro@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---

module: plugin_facts
short_description: Gather specifications of ansible plugins.
description:
    - Offers ability to dynamically gather information about the plugins specifications.
    - Can be used to autobuild playbook, task files, validators, filters, surveys, drifters of inputs
      between ansible releases, etc...
author: Victor da Costa (@victorock)
requirements:
    - Ansible
options:
    name:
        description:
            - Plugin name to gather facts.
        required: False
        aliases: [ 'plugin' ]
    type:
        description:
            - Plugin type to lookup for name.
        default: 'module'
        choices: [ 'module' ]
'''

EXAMPLES = '''
# Example
  - name: "Gather module documentation facts for ios_config"
    plugin_facts:
      name: "ios_config"
    register: plugin_facts

  - name: Build Playbook
    template:
      src: "templates/playbook.j2"
      dest: "playbooks/ios_config.yaml"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.plugin_facts import get_facts

def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', aliases=['plugin'], required=False),
            type=dict(type='str', choices=['module'], required=False, default='module')
        ),
        supports_check_mode=False
    )

    try:
        plugin_facts = get_facts(module.params.get("name"), module.params.get("type"))
    except Exception as e:
        module.fail_json(msg=to_native(e))

    return module.exit_json(plugin=plugin_facts, changed=False)

main()
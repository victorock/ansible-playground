#
# coding: utf-8 -*-
# (c) 2019, Victor da Costa <victorockeiro@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
from ansible import constants as C
import ansible.plugins.loader as plugin_loader
from ansible.plugins.loader import action_loader, fragment_loader
from ansible.errors import AnsibleError
from ansible.utils.plugin_docs import BLACKLIST, get_docstring
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def namespace_from_plugin_filepath(filepath, plugin_name, basedir):
    if not basedir.endswith('/'):
        basedir += '/'
    rel_path = filepath.replace(basedir, '')
    extension_free = os.path.splitext(rel_path)[0]
    namespace_only = extension_free.rsplit(plugin_name, 1)[0].strip('/_')
    clean_ns = namespace_only.replace('/', '.')
    if clean_ns == '':
        clean_ns = None

    return clean_ns

def find_plugins(path, ptype):

    plugin_list = set()

    if not os.path.exists(path):
        return plugin_list

    if not os.path.isdir(path):
        return plugin_list

    bkey = ptype.upper()
    for plugin in os.listdir(path):
        full_path = '/'.join([path, plugin])

        if plugin.startswith('.'):
            continue
        elif os.path.isdir(full_path):
            continue
        elif any(plugin.endswith(x) for x in C.BLACKLIST_EXTS):
            continue
        elif plugin.startswith('__'):
            continue
        elif plugin in C.IGNORE_FILES:
            continue
        elif plugin .startswith('_'):
            if os.path.islink(full_path):  # avoids aliases
                continue

        plugin = os.path.splitext(plugin)[0]  # removes the extension
        plugin = plugin.lstrip('_')  # remove underscore from deprecated plugins

        if plugin not in BLACKLIST.get(bkey, ()):
            plugin_list.add(plugin)

    return plugin_list

def get_all_plugins_of_type(plugin_type):
    loader = getattr(plugin_loader, '%s_loader' % plugin_type)
    plugin_list = set()
    paths = loader._get_paths()
    for path in paths:
        plugins_to_add = find_plugins(path, plugin_type)
        plugin_list.update(plugins_to_add)
    return sorted(set(plugin_list))

def get_plugin_metadata(plugin_type, plugin_name):
    # if the plugin lives in a non-python file (eg, win_X.ps1), require the corresponding python file for docs
    loader = getattr(plugin_loader, '%s_loader' % plugin_type)
    filename = loader.find_plugin(plugin_name, mod_type='.py', ignore_deprecated=True, check_aliases=True)
    if filename is None:
        raise AnsibleError("unable to load {0} plugin named {1} ".format(plugin_type, plugin_name))

    try:
        doc, _, _, metadata = get_docstring(filename, fragment_loader)
    except Exception:
        raise AnsibleError(
            "%s %s at %s hasa documentation error formatting or is missing documentation." %
            (plugin_type, plugin_name, filename))

    if doc is None:
        if 'removed' not in metadata.get('status', []):
            raise AnsibleError(
                "%s %s at %s has a documentation error formatting or is missing documentation." %
                (plugin_type, plugin_name, filename))

        # Removed plugins don't have any documentation
        return None

    return dict(
        spec=doc,
        namespace=namespace_from_plugin_filepath(filename, plugin_name, loader.package_path)
    )

def get_facts(plugin_name=None, plugin_type='module'):

    plugin_facts = {}
    if plugin_name is not None:
        plugin_facts[plugin_name] = get_plugin_metadata(plugin_type, plugin_name)
    else:
        plugin_names = get_all_plugins_of_type(plugin_type)
        for plugin_name in plugin_names:
            plugin_info = get_plugin_metadata(plugin_type, plugin_name)
            if plugin_info is not None:
                plugin_facts[plugin_name] = plugin_info
    
    return plugin_facts

# Copyright 2015 Tesora Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from collections import abc
import os
import re

from trove.common import cfg
from trove.common import pagination
from trove.common import utils
from trove.guestagent.common import operating_system

CONF = cfg.CONF


def update_dict(updates, target):
    """Recursively update a target dictionary with given updates.

    Updates are provided as a dictionary of key-value pairs
    where a value can also be a nested dictionary in which case
    its key is treated as a sub-section of the outer key.
    If a list value is encountered the update is applied
    iteratively on all its items.

    :returns:    Will always return a dictionary of results (may be empty).
    """
    if target is None:
        target = {}

    if isinstance(target, list):
        for index, item in enumerate(target):
            target[index] = update_dict(updates, item)
        return target

    if updates is not None:
        for k, v in updates.items():
            if isinstance(v, abc.Mapping):
                target[k] = update_dict(v, target.get(k, {}))
            else:
                target[k] = updates[k]

    return target


def expand_dict(target, namespace_sep='.'):
    """Expand a flat dict to a nested one.
    This is an inverse of 'flatten_dict'.

    :seealso: flatten_dict
    """
    nested = {}
    for k, v in target.items():
        sub = nested
        keys = k.split(namespace_sep)
        for key in keys[:-1]:
            sub = sub.setdefault(key, {})
        sub[keys[-1]] = v

    return nested


def flatten_dict(target, namespace_sep='.'):
    """Flatten a nested dict.
    Return a one-level dict with all sub-level keys joined by a namespace
    separator.

    The following nested dict:
    {'ns1': {'ns2a': {'ns3a': True, 'ns3b': False}, 'ns2b': 10}}

    would be flattened to:
    {'ns1.ns2a.ns3a': True, 'ns1.ns2a.ns3b': False, 'ns1.ns2b': 10}
    """
    def flatten(target, keys, namespace_sep):
        flattened = {}
        if isinstance(target, abc.Mapping):
            for k, v in target.items():
                flattened.update(
                    flatten(v, keys + [k], namespace_sep))
        else:
            ns = namespace_sep.join(keys)
            flattened[ns] = target

        return flattened

    return flatten(target, [], namespace_sep)


def build_file_path(base_dir, base_name, *extensions):
    """Build a path to a file in a given directory.
    The file may have an extension(s).

    :returns:    Path such as: 'base_dir/base_name.ext1.ext2.ext3'
    """
    file_name = os.extsep.join([base_name] + list(extensions))
    return os.path.expanduser(os.path.join(base_dir, file_name))


def to_bytes(value):
    """Convert numbers with a byte suffix to bytes.
    """
    if isinstance(value, str):
        pattern = re.compile(r'^(\d+)([K,M,G]{1})$')
        match = pattern.match(value)
        if match:
            value = match.group(1)
            suffix = match.group(2)
            factor = {
                'K': 1024,
                'M': 1024 ** 2,
                'G': 1024 ** 3,
            }[suffix]

            return int(round(factor * float(value)))

    return value


def paginate_list(li, limit=None, marker=None, include_marker=False):
    """Paginate a list of objects based on the name attribute.
    :returns:           Page sublist and a marker (name of the last item).
    """
    return pagination.paginate_object_list(
        li, 'name', limit=limit, marker=marker, include_marker=include_marker)


def serialize_list(li, limit=None, marker=None, include_marker=False):
    """
    Paginate (by name) and serialize a given object list.
    :returns:           A serialized and paginated version of a given list.
    """
    page, next_name = paginate_list(li, limit=limit, marker=marker,
                                    include_marker=include_marker)
    return [item.serialize() for item in page], next_name


def get_filesystem_volume_stats(fs_path):
    try:
        stats = os.statvfs(fs_path)
    except OSError:
        raise RuntimeError("Filesystem not found (%s)" % fs_path)

    total = stats.f_blocks * stats.f_bsize
    free = stats.f_bfree * stats.f_bsize
    # return the size in GB
    used_gb = utils.to_gb(total - free)
    total_gb = utils.to_gb(total)

    output = {
        'block_size': stats.f_bsize,
        'total_blocks': stats.f_blocks,
        'free_blocks': stats.f_bfree,
        'total': total_gb,
        'free': free,
        'used': used_gb
    }
    return output


def get_conf_dir():
    """Get the config directory for the database related settings.

    For now, the files inside the config dir are mainly for instance rebuild.
    """
    mount_point = CONF.get(CONF.datastore_manager).mount_point
    conf_dir = os.path.join(mount_point, 'conf.d')
    if not operating_system.exists(conf_dir, is_directory=True, as_root=True):
        operating_system.ensure_directory(conf_dir, as_root=True)

    return conf_dir

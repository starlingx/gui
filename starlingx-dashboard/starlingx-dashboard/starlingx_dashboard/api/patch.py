#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
#
# Copyright (c) 2014-2024 Wind River Systems, Inc.
#

import logging
import six

from six.moves.urllib.parse import urlparse

import requests

from openstack_dashboard.api import base

LOG = logging.getLogger(__name__)


class Client(object):
    def __init__(self, version, url, token_id):
        self.version = version
        self.url = url
        self.token_id = token_id

    def _make_request(self, token_id, method, api_version, api_cmd,
                      encoder=None):
        url = self.url
        url += "/%s/%s" % (api_version, api_cmd)
        # url += "/patch/%s" % (api_cmd)

        headers = {"X-Auth-Token": token_id,
                   "Accept": "application/json"}

        if method == 'GET':
            req = requests.get(url, headers=headers)
        elif method == 'POST':
            if encoder is not None:
                headers['Content-Type'] = encoder.content_type
            req = requests.post(url, headers=headers, data=encoder)

        resp = req.json()

        return resp

    def get_patches(self):
        return self._make_request(self.token_id, "GET", self.version,
                                  "query?show=all")

    def get_hosts(self):
        return self._make_request(self.token_id, "GET", self.version,
                                  "query_hosts")


def _patching_client(request):
    o = urlparse(base.url_for(request, 'patching'))
    url = "://".join((o.scheme, o.netloc))
    return Client("v1", url, token_id=request.user.token.id)


class Patch(object):
    _attrs = ['status',
              'sw_version',
              'install_instructions',
              'description',
              'warnings',
              'summary',
              'repostate',
              'patchstate',
              'requires',
              'unremovable',
              'reboot_required']


class Host(object):
    if six.PY2:
        # Centos
        _attrs = ['hostname',
                  'installed',
                  'ip',
                  'missing_pkgs',
                  'nodetype',
                  'patch_current',
                  'patch_failed',
                  'requires_reboot',
                  'secs_since_ack',
                  'stale_details',
                  'to_remove',
                  'sw_version',
                  'state',
                  'allow_insvc_patching',
                  'interim_state']
    else:
        # Debian
        _attrs = ['hostname',
                  'ip',
                  'latest_sysroot_commit',
                  'nodetype',
                  'patch_current',
                  'patch_failed',
                  'requires_reboot',
                  'secs_since_ack',
                  'stale_details',
                  'sw_version',
                  'state',
                  'allow_insvc_patching',
                  'interim_state']


def get_patches(request):
    patches = []
    try:
        info = _patching_client(request).get_patches()
    except Exception:
        return patches

    if info:
        for p in info['pd'].items():
            patch = Patch()

            for a in patch._attrs:
                if a == 'requires':
                    patch.requires = [str(rp) for rp in p[1][a]]
                    continue

                if a == 'reboot_required':
                    # Default to "N"
                    setattr(patch, a, str(p[1].get(a, "N")))
                    continue

                # Must handle older patches that have metadata that is missing
                # newer attributes. Default missing attributes to "".
                setattr(patch, a, str(p[1].get(a, "")))
            patch.patch_id = str(p[0])

            patches.append(patch)
    return patches


def get_hosts(request):
    hosts = []
    default_value = None
    try:
        info = _patching_client(request).get_hosts()
    except Exception:
        return hosts

    if info:
        for h in info['data']:
            host = Host()
            for a in host._attrs:
                # if host received doesn't have this attribute,
                # add it with a default value
                if hasattr(h, a):
                    setattr(host, a, h[a])
                else:
                    setattr(host, a, default_value)
                    LOG.debug("Attribute not found. Adding default:"
                              "%s", a)
            hosts.append(host)
    return hosts


def get_host(request, hostname):
    phosts = get_hosts(request)
    return next((phost for phost in phosts if phost.hostname == hostname),
                None)

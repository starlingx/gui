#
# Copyright (c) 2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
import logging
from urllib.parse import urlparse

from horizon import messages
from openstack_dashboard.api import base

import requests
from requests_toolbelt import MultipartEncoder

LOG = logging.getLogger(__name__)

USM_API_SERVICENAME = "usm"
USM_API_VERSION = "v1"


class Client(object):
    def __init__(self, version, url, token_id):
        self.version = version
        self.url = url
        self.token_id = token_id

    def _make_request(self, token_id, method, api_version, api_cmd,
                      encoder=None):
        url = self.url
        url += f"/{api_version}/{api_cmd}"

        headers = {"X-Auth-Token": token_id,
                   "Accept": "application/json"}

        if method == 'GET':
            req = requests.get(url, headers=headers)
        elif method == 'POST':
            if encoder is not None:
                headers['Content-Type'] = encoder.content_type
            req = requests.post(url, headers=headers, data=encoder)
        elif method == 'DELETE':
            req = requests.delete(url, headers=headers)

        resp = req.json()

        return resp

    def get_releases(self):
        return self._make_request(self.token_id, "GET", self.version,
                                  "release")

    def get_release(self, release_id):
        return self._make_request(self.token_id, "GET", self.version,
                                  "release/%s" % release_id)

    def get_hosts(self):
        return self._make_request(self.token_id, "GET", self.version,
                                  "deploy_host")

    def install_host(self, hostname):
        return self._make_request(self.token_id, "POST", self.version,
                                  "deploy_host/%s", hostname)

    def upload_release(self, release):
        encoder = MultipartEncoder(fields=release)
        return self._make_request(self.token_id, "POST", self.version,
                                  "release", encoder=encoder)

    def delete_releases(self, release_ids):
        releases = "/".join(release_ids)
        return self._make_request(self.token_id, "DELETE", self.version,
                                  "release/%s" % releases)

    def commit_releases(self, release_ids):
        releases = "/".join(release_ids)
        return self._make_request(self.token_id, "POST", self.version,
                                  "software/commit_patch/%s" % releases)

    def deploy_precheck(self, release_id):
        return self._make_request(self.token_id, "POST", self.version,
                                  "deploy/%s/precheck" % release_id)

    def deploy_start(self, release_id):
        return self._make_request(self.token_id, "POST", self.version,
                                  "deploy/%s/start" % release_id)

    def deploy_activate(self):
        return self._make_request(self.token_id, "POST", self.version,
                                  "deploy/activate")

    def deploy_complete(self):
        return self._make_request(self.token_id, "POST", self.version,
                                  "deploy/complete")

    def deploy_show(self):
        return self._make_request(self.token_id, "GET", self.version,
                                  "deploy")

    def deploy_abort(self):
        return self._make_request(self.token_id, "POST", self.version,
                                  "deploy/abort")

    def deploy_delete(self):
        return self._make_request(self.token_id, "DELETE", self.version,
                                  "deploy")

    def deploy_host_rollback(self, hostname):
        return self._make_request(self.token_id, "POST", self.version,
                                  "deploy_host/%s/rollback" % hostname)


def _usm_client(request):
    o = urlparse(base.url_for(request, USM_API_SERVICENAME))
    url = "://".join((o.scheme, o.netloc))
    return Client(USM_API_VERSION, url, token_id=request.user.token.id)


class Release(object):
    _attrs = ['release_id',
              'state',
              'sw_version',
              'status',
              'unremovable',
              'summary',
              'description',
              'install_instructions',
              'warnings',
              'reboot_required',
              'requires']

    @property
    def attrs(self):
        return self._attrs


class Host(object):
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

    @property
    def attrs(self):
        return self._attrs


class DeployHost(object):
    _attrs = [
        'hostname',
        'software_release',
        'target_release',
        'reboot_required',
        'host_state'
    ]

    @property
    def attrs(self):
        return self._attrs


def get_releases(request):
    releases = []
    try:
        info = _usm_client(request).get_releases()
    except Exception:
        return releases

    if info:
        for r in info:
            release = Release()

            for a in release.attrs:
                if a == 'requires':
                    release.requires = [str(rs) for rs in r[a]]
                    continue
                if a == 'reboot_required':
                    # Default to "false"
                    setattr(release, a, str(r.get(a, "false")))
                    continue
                setattr(release, a, str(r.get(a, "")))
            releases.append(release)
    return releases


def get_release(request, release_id):
    data = _usm_client(request).get_release(release_id)
    release = Release()
    for attr, value in data.items():
        setattr(release, attr, value)
    return release


def get_deploy_hosts(request):
    deploy_hosts = []

    try:
        info = _usm_client(request).get_hosts()
    except Exception:
        return deploy_hosts

    for dh in info:
        deploy_host = DeployHost()
        for attr, value in dh.items():
            setattr(deploy_host, attr, value)
        deploy_hosts.append(deploy_host)
    return deploy_hosts


def get_host(request, hostname):
    phosts = get_deploy_hosts(request)
    return next((phost for phost in phosts if phost.hostname == hostname),
                None)


def get_message(request, data):
    data_msg = f"RESPONSE: {data}"
    LOG.info(data_msg)
    if not data or data.get('error'):
        error_msg = data.get('error', "Invalid release file")
        messages.error(request, error_msg)
        LOG.error(error_msg)
    if data.get('warning'):
        return data["warning"]
    if data.get('info'):
        return data["info"]
    return ""


def host_install(request, hostname):
    resp = _usm_client(request).install_host(hostname)
    return get_message(request, resp)


def release_upload_req(request, release, name,
                       release_extra=None, name_extra=None):
    _file = {
        'file': (name, release),
    }
    # iso and sig file should be in the same body for upload
    if release_extra is not None and name_extra is not None:
        _file['file_1'] = (name_extra, release_extra)
    resp = _usm_client(request).upload_release(_file)
    return get_message(request, resp)


def release_delete_req(request, release_id):
    resp = _usm_client(request).delete_releases(release_id)
    return get_message(request, resp)


def release_commit_req(request, release_id):
    resp = _usm_client(request).commit_releases(release_id)
    return get_message(request, resp)


def deploy_start_req(request, release_id):
    resp = _usm_client(request).deploy_start(release_id)
    return get_message(request, resp)


def deploy_precheck_req(request, release_id):
    resp = _usm_client(request).deploy_precheck(release_id)
    return get_message(request, resp)


def deploy_complete_req(request):
    resp = _usm_client(request).deploy_complete()
    return get_message(request, resp)


def deploy_activate_req(request):
    resp = _usm_client(request).deploy_activate()
    return get_message(request, resp)


def deploy_show_req(request):
    resp = _usm_client(request).deploy_show()
    return resp


def deploy_abort_req(request):
    resp = _usm_client(request).deploy_abort()
    return get_message(request, resp)


def deploy_delete_req(request):
    resp = _usm_client(request).deploy_delete()
    return get_message(request, resp)


def deploy_rollback_req(request, hostname):
    resp = _usm_client(request).deploy_host_rollback(hostname)
    return get_message(request, resp)

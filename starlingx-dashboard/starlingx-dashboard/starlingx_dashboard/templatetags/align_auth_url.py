#
# Copyright (c) 2020-2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from dcmanagerclient.api.v1 import client
from django import template
from openstack_dashboard.api import base

register = template.Library()
AUTH_PORT = '5000'


def align_ip_port(url, ip):
    url_list = url.split('//')
    url_list[-1] = ip
    return '//'.join(url_list) + ':' + AUTH_PORT


@register.filter(name="align_auth_url")
def align_auth_url(auth_url):
    url_list = auth_url.split(':')
    url_list[-1] = AUTH_PORT
    return ':'.join(url_list)


@register.simple_tag(name='align_subcloud_auth_url', takes_context=True)
def align_subcloud_auth_url(context, auth_url):
    try:
        request = context["request"]
        subcloud_name = request.COOKIES.get("subcloud_" +
                                            request.user.services_region)
        request.user.services_region = 'SystemController'
        endpoint = base.url_for(request, 'dcmanager')
        dc_manager = client.Client(project_id=request.user.project_id,
                                   user_id=request.user.id,
                                   auth_token=request.user.token.id,
                                   dcmanager_url=endpoint)
        result = dc_manager.subcloud_manager.\
            subcloud_additional_details(subcloud_name)
        subcloud_oam_floating_ip = result[0].oam_floating_ip
        return align_ip_port(auth_url, subcloud_oam_floating_ip)
    except Exception:
        return auth_url

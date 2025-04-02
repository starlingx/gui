#
# Copyright (c) 2017-2025 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import ipaddress
import uuid

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import views

from openstack_dashboard.api import base
from starlingx_dashboard import api as stx_api


def _get_service_port(url):
    url_list = url.split('://')
    ip = url_list[-1]

    return ip.split(':')[-1]


def _format_ip_addr(ip_address_string):
    """Add brackets if an IPv6 address"""
    ip = ipaddress.ip_address(ip_address_string)
    if isinstance(ip, ipaddress.IPv6Address):
        return f"[{ip_address_string}]"
    return ip_address_string


def _build_endpoint(endpoint_url, subcloud_ip, region_name):
    service_port = _get_service_port(endpoint_url)
    subcloud_ip = _format_ip_addr(subcloud_ip)

    new_endpoint = {
        "id": str(uuid.uuid4()),
        "interface": "admin",
        "region_id": region_name,
        "url": f"https://{subcloud_ip}:{service_port}",
        "region": region_name,
    }

    return new_endpoint


class IndexView(views.HorizonTemplateView):
    template_name = 'dc_admin/cloud_overview/index.html'
    page_title = 'Cloud Overview'

    def get_subclouds(self):
        try:
            return stx_api.dc_manager.subcloud_list(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve subclouds.'))
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        subclouds = self.get_subclouds()

        if subclouds:
            subcloud_service_types = [
                "platform",
                "faultmanagement",
                "identity",
                "nfv",
                "usm",
                "patching"
            ]
            for subcloud in subclouds:
                for service in self.request.user.service_catalog:
                    if service["type"] in subcloud_service_types:
                        endpoint = base.url_for(
                            self.request,
                            service["type"],
                            endpoint_type="admin",
                            region=getattr(
                                settings, "REGION_ONE_NAME", "RegionOne"
                            ),
                        )
                        service["endpoints"].append(_build_endpoint(
                            endpoint,
                            subcloud.management_start_ip,
                            subcloud.region_name)
                        )

        return context

    def render_to_response(self, context):
        response = super().render_to_response(context)
        response.set_cookie(
            "region_one_name",
            getattr(settings, "REGION_ONE_NAME", "RegionOne"),
        )
        return response

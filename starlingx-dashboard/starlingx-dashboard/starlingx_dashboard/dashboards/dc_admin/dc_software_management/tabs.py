#
# Copyright (c) 2018-2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from starlingx_dashboard import api
from starlingx_dashboard.dashboards.dc_admin.dc_software_management \
    import tables as tables

LOG = logging.getLogger(__name__)


class ReleasesTab(tabs.TableTab):
    table_classes = (tables.ReleasesTable,)
    name = _("Releases")
    slug = "releases"
    template_name = "dc_admin/dc_software_management/_releases.html"
    preload = False

    def get_dc_releases_data(self):
        request = self.request
        releases = []
        try:
            releases = api.usm.get_releases(request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve release list.'))

        return releases


class DCSoftwareManagementTabs(tabs.TabGroup):
    slug = "dc_software_management_tabs"
    tabs = (ReleasesTab,)
    sticky = True

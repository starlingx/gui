#
# Copyright (c) 2018-2022 Wind River Systems, Inc.
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


class PatchesTab(tabs.TableTab):
    table_classes = (tables.PatchesTable,)
    name = _("Patches")
    slug = "patches"
    template_name = ("dc_admin/dc_software_management/_patches.html")
    preload = False

    def get_dc_patches_data(self):
        request = self.request
        patches = []
        try:
            patches = api.patch.get_patches(request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve patch list.'))

        return patches


class DCSoftwareManagementTabs(tabs.TabGroup):
    slug = "dc_software_management_tabs"
    tabs = (PatchesTab,)
    sticky = True

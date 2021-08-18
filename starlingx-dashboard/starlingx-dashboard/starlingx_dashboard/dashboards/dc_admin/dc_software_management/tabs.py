#
# Copyright (c) 2018-2021 Wind River Systems, Inc.
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


class CloudOrchestrationTab(tabs.TableTab):
    table_classes = (tables.CloudPatchStepsTable,)
    name = _("Cloud Strategy Orchestration")
    slug = "cloud_strategy_orchestration"
    template_name = ("dc_admin/dc_software_management/"
                     "_cloud_strategy_orchestration.html")
    preload = False

    def get_context_data(self, request):
        context = super(CloudOrchestrationTab, self).\
            get_context_data(request)

        strategy = None
        try:
            strategy = api.dc_manager.get_strategy(request)
        except Exception as ex:
            LOG.exception(ex)
            exceptions.handle(request,
                              _('Unable to retrieve current strategy.'))
        context['strategy'] = strategy
        return context

    def get_cloudpatchsteps_data(self):
        request = self.request
        steps = []
        try:
            steps = api.dc_manager.step_list(request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve steps list.'))

        return steps


class CloudPatchConfigTab(tabs.TableTab):
    table_classes = (tables.CloudPatchConfigTable,)
    name = _("Cloud Patching Configuration")
    slug = "cloud_patch_config"
    template_name = ("dc_admin/dc_software_management/"
                     "_cloud_patch_config.html")
    preload = False

    def get_cloudpatchconfig_data(self):
        request = self.request
        steps = []
        try:
            steps = api.dc_manager.config_list(request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve configuration list.'))

        return steps


class SubcloudGroupTab(tabs.TableTab):
    table_classes = (tables.SubcloudGroupManagamentTable,)
    name = _("Subcloud Group Management")
    slug = "subcloud_group_managment"
    template_name =\
        ("dc_admin/dc_software_management/_subcloud_group_mgmt.html")
    preload = False

    def get_subcloudgroupmgmt_data(self):
        request = self.request
        groups = []
        try:
            groups = api.dc_manager.list_subcloud_groups(request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve subcloud group list.'))
        return groups


class DCSoftwareManagementTabs(tabs.TabGroup):
    slug = "dc_software_management_tabs"
    tabs = (PatchesTab, CloudOrchestrationTab,
            CloudPatchConfigTab, SubcloudGroupTab)
    sticky = True

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
from starlingx_dashboard.dashboards.dc_admin.dc_orchestration \
    import tables as tables

LOG = logging.getLogger(__name__)


class CloudOrchestrationTab(tabs.TableTab):
    table_classes = (tables.CloudPatchStepsTable,)
    name = _("Orchestration Strategy")
    slug = "cloud_strategy_orchestration"
    template_name = ("dc_admin/dc_orchestration/"
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
    name = _("Cloud Patching Configurations")
    slug = "cloud_patch_config"
    template_name = ("dc_admin/dc_orchestration/"
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
    table_classes = (tables.SubcloudGroupManagementTable,)
    name = _("Subcloud Group Management")
    slug = "subcloud_group_managment"
    template_name =\
        ("dc_admin/dc_orchestration/_subcloud_group_mgmt.html")
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
    slug = "dc_orchestration_tabs"
    tabs = (CloudOrchestrationTab, CloudPatchConfigTab, SubcloudGroupTab)
    sticky = True

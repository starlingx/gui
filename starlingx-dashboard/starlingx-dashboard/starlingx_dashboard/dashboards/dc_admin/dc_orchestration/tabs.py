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


class SubcloudStrategyConfigTab(tabs.TableTab):
    table_classes = (tables.SubcloudStrategyConfigTable,)
    name = _("Subcloud Strategy Configurations")
    slug = "subcloud_strategy_config"
    template_name = ("dc_admin/dc_orchestration/"
                     "_subcloud_strategy_config.html")
    preload = False

    def get_subcloudstrategyconfig_data(self):
        request = self.request
        steps = []
        try:
            steps = api.dc_manager.config_list(request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve configuration list.'))

        return steps


class SubcloudGroupTab(tabs.TableTab):
    table_classes = (tables.SubcloudGroupsTable,)
    name = _("Subcloud Groups")
    slug = "subcloud_groups"
    template_name =\
        ("dc_admin/dc_orchestration/_subcloud_groups.html")
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
    tabs = (CloudOrchestrationTab, SubcloudStrategyConfigTab, SubcloudGroupTab)
    sticky = True

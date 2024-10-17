#
# Copyright (c) 2013-2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from starlingx_dashboard import api as stx_api
from starlingx_dashboard.dashboards.admin.software_management import \
    tables as toplevel_tables

LOG = logging.getLogger(__name__)


class BaseReleasesTab(tabs.TableTab):
    def get_releases_data(self, request=None):
        if request is None:
            request = self.request
        releases = []
        try:
            releases = stx_api.usm.get_releases(request)
        except Exception:
            exceptions.handle(request, _('Unable to retrieve release list.'))

        if releases:
            for release in releases:
                if release.state in ['deploying', 'removing']:
                    deploy_show_data = None
                    try:
                        deploy_show_data = stx_api.usm.deploy_show_req(request)
                    except Exception:
                        exceptions.handle(
                            request,
                            _('Unable to retrieve release deploy list.')
                        )
                    release.deploy_host_state = None
                    if deploy_show_data:
                        deploy_host_release = deploy_show_data[0]
                        release.deploy_host_state = deploy_host_release[
                            'state']
        return releases


class ReleasesTab(BaseReleasesTab):
    table_classes = (toplevel_tables.ReleasesTable,)
    name = _("Releases")
    slug = "releases"
    template_name = "admin/software_management/_releases.html"

    def get_context_data(self, request):
        context = super(ReleasesTab, self).get_context_data(request)

        phosts = []
        try:
            phosts = stx_api.usm.get_deploy_hosts(request)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve host list.'))

        context['patch_current'] = True if not phosts else False

        return context


class DeployOrchestrationTab(tabs.TableTab):
    table_classes = (toplevel_tables.SoftwareDeployStagesTable,)
    name = _("Deploy Orchestration")
    slug = "deploy_orchestration"
    template_name = ("admin/software_management/_deploy_orchestration.html")

    def get_context_data(self, request):
        context = super(DeployOrchestrationTab, self).get_context_data(
            request)

        strategy = None
        try:
            strategy = stx_api.vim.get_strategy(
                request, stx_api.vim.STRATEGY_SW_DEPLOY)
        except Exception as ex:
            LOG.exception(ex)
            exceptions.handle(request,
                              _('Unable to retrieve current strategy.'))

        context['strategy'] = strategy
        return context

    def get_softwaredeploystages_data(self):
        request = self.request
        stages = []
        try:
            stages = stx_api.vim.get_stages(request,
                                            stx_api.vim.STRATEGY_SW_DEPLOY)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve stages list.'))

        return stages

    def allowed(self, request):
        if request.user.services_region == 'SystemController':
            return False
        return True


class SoftwareManagementTabs(tabs.TabGroup):
    slug = "software_management_tabs"
    tabs = (ReleasesTab, DeployOrchestrationTab)
    sticky = True

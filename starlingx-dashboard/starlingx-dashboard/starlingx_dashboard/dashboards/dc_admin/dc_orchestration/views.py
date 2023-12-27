#
# Copyright (c) 2018-2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import datetime
import logging

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tabs

from starlingx_dashboard import api
from starlingx_dashboard.dashboards.admin.software_management.views import \
    DetailPatchView as AdminDetailPatchView
from starlingx_dashboard.dashboards.dc_admin.dc_orchestration.forms \
    import ApplyCloudStrategyForm
from starlingx_dashboard.dashboards.dc_admin.dc_orchestration.forms \
    import CreateCloudStrategyForm
from starlingx_dashboard.dashboards.dc_admin.dc_orchestration.forms \
    import CreateSubcloudConfigForm
from starlingx_dashboard.dashboards.dc_admin.dc_orchestration.forms \
    import CreateSubcloudGroupForm
from starlingx_dashboard.dashboards.dc_admin.dc_orchestration.forms \
    import UpdateSubcloudGroupForm
from starlingx_dashboard.dashboards.dc_admin.dc_orchestration.tabs \
    import DCSoftwareManagementTabs

LOG = logging.getLogger(__name__)

STRATEGY_VALID_TIME_IN_MINUTES = 60


class IndexView(tabs.TabbedTableView):
    tab_group_class = DCSoftwareManagementTabs
    template_name = 'dc_admin/dc_orchestration/index.html'
    page_title = _("Orchestration")

    def get_tabs(self, request, *args, **kwargs):
        return self.tab_group_class(request, **kwargs)


class DetailPatchView(AdminDetailPatchView):
    template_name = 'dc_admin/dc_orchestration/_detail_patches.html'
    failure_url = 'horizon:dc_admin:dc_orchestration:index'


class CreateCloudStrategyView(forms.ModalFormView):
    form_class = CreateCloudStrategyForm
    template_name = 'dc_admin/dc_orchestration/' \
                    'create_cloud_strategy.html'
    context_object_name = 'strategy'
    success_url = reverse_lazy("horizon:dc_admin:dc_orchestration:index")


def check_strategy_out_of_date(strategy_time_str,
                               timeout_minutes=STRATEGY_VALID_TIME_IN_MINUTES,
                               date_format='%Y-%m-%d %H:%M:%S.%f'):
    creation_time = datetime.datetime.strptime(strategy_time_str, date_format)
    now = datetime.datetime.now()
    minutes = (now - creation_time).total_seconds() // 60
    outdated = False
    if minutes > timeout_minutes:
        outdated = True
    return outdated, int(minutes // 60), int(minutes % 60)


class ApplyCloudStrategyView(forms.ModalFormView):
    form_class = ApplyCloudStrategyForm
    template_name = 'dc_admin/dc_orchestration/' \
                    'apply_cloud_strategy.html'
    context_object_name = 'strategy'
    success_url = reverse_lazy("horizon:dc_admin:dc_orchestration:index")

    def get_context_data(self, **kwargs):
        context = super(ApplyCloudStrategyView, self).get_context_data(
            **kwargs)
        strategy = None
        try:
            strategy = api.dc_manager.get_strategy(self.request)
        except Exception as ex:
            LOG.exception(ex)
            exceptions.handle(self.request,
                              _('Unable to retrieve current strategy.'))
        context['out_of_date'], context['hours'], context['minutes'] = \
            check_strategy_out_of_date(strategy.created_at)
        return context


class CreateSubcloudStrategyConfigView(forms.ModalFormView):
    form_class = CreateSubcloudConfigForm
    template_name = 'dc_admin/dc_orchestration/' \
                    'create_subcloud_strategy_config.html'
    context_object_name = 'config'
    success_url = reverse_lazy("horizon:dc_admin:dc_orchestration:index")


class EditSubCloudStrategyConfigView(forms.ModalFormView):
    form_class = CreateSubcloudConfigForm
    template_name = 'dc_admin/dc_orchestration/' \
                    'edit_subcloud_strategy_config.html'
    context_object_name = 'config'
    success_url = reverse_lazy("horizon:dc_admin:dc_orchestration:index")

    def get_context_data(self, **kwargs):
        context = super(EditSubCloudStrategyConfigView, self).get_context_data(
            **kwargs)
        context['subcloud'] = self.kwargs['subcloud']
        return context

    def get_initial(self):
        try:
            config = api.dc_manager.config_get(self.request,
                                               self.kwargs['subcloud'])
        except Exception:
            exceptions.handle(self.request, _("Unable to retrieve subcloud "
                                              "configuration data."))

        return {'subcloud': config.cloud,
                'storage_apply_type': config.storage_apply_type,
                'worker_apply_type': config.worker_apply_type,
                'max_parallel_workers': config.max_parallel_workers,
                'default_instance_action': config.default_instance_action,
                'alarm_restriction_type': config.alarm_restriction_type}


class CreateSubcloudGroupView(forms.ModalFormView):
    form_class = CreateSubcloudGroupForm
    template_name = 'dc_admin/dc_orchestration/' \
                    'create_subcloud_group.html'
    success_url = reverse_lazy("horizon:dc_admin:dc_orchestration:index")


class EditSubcloudGroupView(forms.ModalFormView):
    form_class = UpdateSubcloudGroupForm
    template_name = 'dc_admin/dc_orchestration/' \
                    'edit_subcloud_group.html'
    success_url = reverse_lazy("horizon:dc_admin:dc_orchestration:index")

    def get_context_data(self, **kwargs):
        context = super(EditSubcloudGroupView, self).get_context_data(
            **kwargs)
        context['subcloud_group'] = self.kwargs['subcloud_group']
        return context

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            subcloud_group = self.kwargs['subcloud_group']
            try:
                self._object = api.dc_manager.subcloud_group_get(
                    self.request, subcloud_group)
            except Exception:
                redirect = self.success_url
                msg = _('Unable to retrieve subcloud group details.')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_initial(self):
        group = self._get_object()
        return {'name': group.name,
                'description': group.description,
                'group_id': group.group_id,
                'update_apply_type': group.update_apply_type,
                'max_parallel_subclouds': group.max_parallel_subclouds}

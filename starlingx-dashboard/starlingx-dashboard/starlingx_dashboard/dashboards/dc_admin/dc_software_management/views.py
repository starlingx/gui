#
# Copyright (c) 2018-2021 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tabs

from starlingx_dashboard import api
from starlingx_dashboard.dashboards.admin.software_management.views import \
    DetailPatchView as AdminDetailPatchView
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.forms \
    import CreateCloudPatchConfigForm
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.forms \
    import CreateCloudPatchStrategyForm
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.forms \
    import CreateSubcloudGroupForm
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.forms \
    import UpdateSubcloudGroupForm
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.forms \
    import UploadPatchForm
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.tabs \
    import DCSoftwareManagementTabs

LOG = logging.getLogger(__name__)


class IndexView(tabs.TabbedTableView):
    tab_group_class = DCSoftwareManagementTabs
    template_name = 'dc_admin/dc_software_management/index.html'
    page_title = _("Software Management")

    def get_tabs(self, request, *args, **kwargs):
        return self.tab_group_class(request, **kwargs)


class UploadPatchView(forms.ModalFormView):
    form_class = UploadPatchForm
    template_name = 'dc_admin/dc_software_management/upload_patch.html'
    context_object_name = 'patch'
    success_url = reverse_lazy("horizon:dc_admin:dc_software_management:index")


class DetailPatchView(AdminDetailPatchView):
    template_name = 'dc_admin/dc_software_management/_detail_patches.html'
    failure_url = 'horizon:dc_admin:dc_software_management:index'


class CreateCloudPatchStrategyView(forms.ModalFormView):
    form_class = CreateCloudPatchStrategyForm
    template_name = 'dc_admin/dc_software_management/' \
                    'create_cloud_patch_strategy.html'
    context_object_name = 'strategy'
    success_url = reverse_lazy("horizon:dc_admin:dc_software_management:index")


class CreateCloudPatchConfigView(forms.ModalFormView):
    form_class = CreateCloudPatchConfigForm
    template_name = 'dc_admin/dc_software_management/' \
                    'create_cloud_patch_config.html'
    context_object_name = 'config'
    success_url = reverse_lazy("horizon:dc_admin:dc_software_management:index")


class EditCloudPatchConfigView(forms.ModalFormView):
    form_class = CreateCloudPatchConfigForm
    template_name = 'dc_admin/dc_software_management/' \
                    'edit_cloud_patch_config.html'
    context_object_name = 'config'
    success_url = reverse_lazy("horizon:dc_admin:dc_software_management:index")

    def get_context_data(self, **kwargs):
        context = super(EditCloudPatchConfigView, self).get_context_data(
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
    template_name = 'dc_admin/dc_software_management/' \
                    'create_subcloud_group.html'
    success_url = reverse_lazy("horizon:dc_admin:dc_software_management:index")


class EditSubcloudGroupView(forms.ModalFormView):
    form_class = UpdateSubcloudGroupForm
    template_name = 'dc_admin/dc_software_management/' \
                    'edit_subcloud_group.html'
    success_url = reverse_lazy("horizon:dc_admin:dc_software_management:index")

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

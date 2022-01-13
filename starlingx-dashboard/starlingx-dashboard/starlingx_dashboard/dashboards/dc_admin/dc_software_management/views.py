#
# Copyright (c) 2018-2022 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import forms
from horizon import tabs

from starlingx_dashboard.dashboards.admin.software_management.views import \
    DetailPatchView as AdminDetailPatchView
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.forms \
    import UploadPatchForm
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.tabs \
    import DCSoftwareManagementTabs

LOG = logging.getLogger(__name__)

STRATEGY_VALID_TIME_IN_MINUTES = 60


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

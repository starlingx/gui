#
# Copyright (c) 2018-2022 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.conf.urls import url

from starlingx_dashboard.dashboards.dc_admin.dc_software_management.views \
    import DetailPatchView
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.views \
    import IndexView
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.views \
    import UploadPatchView

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^(?P<patch_id>[^/]+)/patchdetail/$',
        DetailPatchView.as_view(), name='dc_patchdetail'),
    url(r'^dc_patchupload/$', UploadPatchView.as_view(),
        name='dc_patchupload'),
]

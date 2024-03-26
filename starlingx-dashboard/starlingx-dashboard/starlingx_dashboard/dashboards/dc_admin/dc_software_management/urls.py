#
# Copyright (c) 2018-2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.conf.urls import url

from starlingx_dashboard.dashboards.dc_admin.dc_software_management.views \
    import DetailReleaseView
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.views \
    import IndexView
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.views \
    import UploadReleaseView

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^(?P<release_id>[^/]+)/releasedetail/$',
        DetailReleaseView.as_view(), name='dc_releasedetail'),
    url(r'^dc_releaseupload/$', UploadReleaseView.as_view(),
        name='dc_releaseupload'),
]

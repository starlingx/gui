#
# Copyright (c) 2018-2021 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.conf.urls import url

from starlingx_dashboard.dashboards.dc_admin.dc_software_management.views \
    import CreateCloudPatchConfigView
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.views \
    import CreateCloudStrategyView
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.views \
    import CreateSubcloudGroupView
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.views \
    import DetailPatchView
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.views \
    import EditCloudPatchConfigView
from starlingx_dashboard.dashboards.dc_admin.dc_software_management.views \
    import EditSubcloudGroupView
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
    url(r'^createcloudstrategy/$', CreateCloudStrategyView.as_view(),
        name='createcloudstrategy'),
    url(r'^createcloudpatchconfig/$', CreateCloudPatchConfigView.as_view(),
        name='createcloudpatchconfig'),
    url(r'^(?P<subcloud>[^/]+)/editcloudpatchconfig/$',
        EditCloudPatchConfigView.as_view(),
        name='editcloudpatchconfig'),
    url(r'^createsubcloudgroup/$', CreateSubcloudGroupView.as_view(),
        name='createsubcloudgroup'),
    url(r'^(?P<subcloud_group>[^/]+)/editsubcloudgroup/$',
        EditSubcloudGroupView.as_view(),
        name='editsubcloudgroup'),
]

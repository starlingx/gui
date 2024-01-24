#
# Copyright (c) 2018-2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.conf.urls import url

from starlingx_dashboard.dashboards.dc_admin.dc_orchestration.views \
    import ApplyCloudStrategyView
from starlingx_dashboard.dashboards.dc_admin.dc_orchestration.views \
    import CreateCloudStrategyView
from starlingx_dashboard.dashboards.dc_admin.dc_orchestration.views \
    import CreateSubcloudGroupView
from starlingx_dashboard.dashboards.dc_admin.dc_orchestration.views \
    import CreateSubcloudStrategyConfigView
from starlingx_dashboard.dashboards.dc_admin.dc_orchestration.views \
    import DetailPatchView
from starlingx_dashboard.dashboards.dc_admin.dc_orchestration.views \
    import EditSubcloudGroupView
from starlingx_dashboard.dashboards.dc_admin.dc_orchestration.views \
    import EditSubCloudStrategyConfigView
from starlingx_dashboard.dashboards.dc_admin.dc_orchestration.views \
    import IndexView

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^(?P<patch_id>[^/]+)/patchdetail/$',
        DetailPatchView.as_view(), name='dc_patchdetail'),
    url(r'^createcloudstrategy/$', CreateCloudStrategyView.as_view(),
        name='createcloudstrategy'),
    url(r'^applycloudstrategy/$', ApplyCloudStrategyView.as_view(),
        name='applycloudstrategy'),
    url(r'^createsubcloudstrategyconfig/$',
        CreateSubcloudStrategyConfigView.as_view(),
        name='createsubcloudstrategyconfig'),
    url(r'^(?P<subcloud>[^/]+)/editsubcloudstrategyconfig/$',
        EditSubCloudStrategyConfigView.as_view(),
        name='editsubcloudstrategyconfig'),
    url(r'^createsubcloudgroup/$', CreateSubcloudGroupView.as_view(),
        name='createsubcloudgroup'),
    url(r'^(?P<subcloud_group>[^/]+)/editsubcloudgroup/$',
        EditSubcloudGroupView.as_view(),
        name='editsubcloudgroup'),
]

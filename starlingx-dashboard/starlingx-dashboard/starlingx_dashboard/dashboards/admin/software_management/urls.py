#
# Copyright (c) 2013-2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.conf.urls import url

from starlingx_dashboard.dashboards.admin.software_management.views import \
    CreatePatchStrategyView
from starlingx_dashboard.dashboards.admin.software_management.views import \
    CreateUpgradeStrategyView
from starlingx_dashboard.dashboards.admin.software_management.views import \
    DetailPatchStageView
from starlingx_dashboard.dashboards.admin.software_management.views import \
    DetailReleaseView
from starlingx_dashboard.dashboards.admin.software_management.views import \
    DetailUpgradeStageView
from starlingx_dashboard.dashboards.admin.software_management.views import \
    IndexView
from starlingx_dashboard.dashboards.admin.software_management.views import \
    UploadReleaseView


urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^(?P<release_id>[^/]+)/releasedetail/$',
        DetailReleaseView.as_view(), name='releasedetail'),
    url(r'^releaseupload/$', UploadReleaseView.as_view(),
        name='releaseupload'),
    url(r'^(?P<stage_id>[^/]+)/phase/(?P<phase>[^/]+)/patchstagedetail/$',
        DetailPatchStageView.as_view(), name='patchstagedetail'),
    url(r'^(?P<stage_id>[^/]+)/phase/(?P<phase>[^/]+)/upgradestagedetail/$',
        DetailUpgradeStageView.as_view(), name='upgradestagedetail'),
    url(r'^createpatchstrategy/$', CreatePatchStrategyView.as_view(),
        name='createpatchstrategy'),
    url(r'^createupgradestrategy/$', CreateUpgradeStrategyView.as_view(),
        name='createupgradestrategy')
]

#
# Copyright (c) 2013-2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.conf.urls import url

from starlingx_dashboard.dashboards.admin.software_management.views import \
    CreateSoftwareDeployStrategyView
from starlingx_dashboard.dashboards.admin.software_management.views import \
    DetailReleaseView
from starlingx_dashboard.dashboards.admin.software_management.views import \
    DetailSoftwareDeployStageView
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
    url(r'^(?P<stage_id>[^/]+)/phase/(?P<phase>[^/]+)\
        /softwaredeploystagedetail/$',
        DetailSoftwareDeployStageView.as_view(),
        name='softwaredeploystagedetail'),
    url(r'^createsoftwaredeploystrategy/$',
        CreateSoftwareDeployStrategyView.as_view(),
        name='create_software_deploy_strategy')
]

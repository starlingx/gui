#
# Copyright (c) 2017, 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


from django.urls import re_path as url

from starlingx_dashboard.dashboards.dc_admin.cloud_overview import views


urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
]

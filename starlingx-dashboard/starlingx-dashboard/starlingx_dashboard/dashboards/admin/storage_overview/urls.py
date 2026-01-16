#
# Copyright (c) 2016, 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.urls import re_path as url

from starlingx_dashboard.dashboards.admin.storage_overview import views

urlpatterns = [
    url(r'^$', views.StorageOverview.as_view(), name='index')
]

# Copyright (c) 2015-2018, 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.urls import re_path as url  # noqa

from starlingx_dashboard.dashboards.admin.inventory.storages.lvg_params \
    import views

urlpatterns = [
    url(r'^(?P<key>[^/]+)/edit/$', views.EditView.as_view(),
        name='edit')]

app_name = "edit"

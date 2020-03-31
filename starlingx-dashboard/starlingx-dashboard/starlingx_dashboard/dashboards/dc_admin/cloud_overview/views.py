#
# Copyright (c) 2017-2020 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


from horizon import views


class IndexView(views.HorizonTemplateView):
    template_name = 'dc_admin/cloud_overview/index.html'
    page_title = 'Cloud Overview'

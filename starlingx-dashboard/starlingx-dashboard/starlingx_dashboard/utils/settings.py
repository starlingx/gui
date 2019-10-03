#
#  Copyright (c) 2019 Wind River Systems, Inc.
#
#  SPDX-License-Identifier: Apache-2.0
#

from django.conf import settings

import horizon
from horizon import base


def get_user_home(user):
    dashboard = horizon.get_default_dashboard()
    dc_mode = getattr(settings, 'DC_MODE', False)

    if user.is_superuser:
        if getattr(user, 'services_region', None) == 'SystemController':
            try:
                dashboard = horizon.get_dashboard('dc_admin')
            except base.NotRegistered:
                pass

    if getattr(user, 'services_region', None) == 'RegionOne' and dc_mode:
        try:
            if user.is_superuser:
                dashboard = horizon.get_dashboard('admin'). \
                    get_panel("inventory")
            else:
                dashboard = horizon.get_dashboard('project'). \
                    get_panel("api_access")
        except base.NotRegistered:
            pass

    return dashboard.get_absolute_url()

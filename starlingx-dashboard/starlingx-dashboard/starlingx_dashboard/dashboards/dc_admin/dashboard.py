#
# Copyright (c) 2017-2022 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


from django.utils.translation import ugettext_lazy as _

import horizon

# Load the api rest services into Horizon
import starlingx_dashboard.api.rest  # noqa: F401 pylint: disable=unused-import


class DCAdmin(horizon.Dashboard):
    name = _("Distributed Cloud Admin")
    slug = "dc_admin"
    default_panel = 'cloud_overview'

    # Must be in the dcmanager's service region to view this dashboard
    permissions = ('openstack.roles.reader',
                   'openstack.services.dcmanager',)

    def allowed(self, context):
        # Must be in SystemController region
        if context['request'].user.services_region != 'SystemController':
            return False

        return super(DCAdmin, self).allowed(context)


horizon.register(DCAdmin)

#
# Copyright (c) 2018-2022 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.utils.translation import ugettext_lazy as _

import horizon
from starlingx_dashboard.dashboards.dc_admin import dashboard


class DCOrchestration(horizon.Panel):
    name = _("Orchestration")
    slug = 'dc_orchestration'

    def allowed(self, context):
        if context['request'].user.services_region != 'SystemController':
            return False

        return super(DCOrchestration, self).allowed(context)

    def nav(self, context):
        if context['request'].user.services_region != 'SystemController':
            return False

        return super(DCOrchestration, self).allowed(context)


dashboard.DCAdmin.register(DCOrchestration)

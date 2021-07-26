#
# Copyright (c) 2021 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import horizon

admin_dashboard = horizon.get_dashboard("admin")
admin_dashboard.policy_rules = (('identity', ''),
                                ('image', ''),
                                ('volume', ''),
                                ('compute', ''),
                                ('network', ''))

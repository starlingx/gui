#
# Copyright (c) 2018-2022 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from starlingx_dashboard.dashboards.admin.software_management.forms \
    import UploadPatchForm as AdminPatchForm

LOG = logging.getLogger(__name__)


class UploadPatchForm(AdminPatchForm):
    failure_url = 'horizon:dc_admin:dc_software_management:index'

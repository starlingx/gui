#
# Copyright (c) 2018-2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import tables

from starlingx_dashboard.dashboards.admin.software_management import tables \
    as AdminTables

LOG = logging.getLogger(__name__)


# Releasing
class UploadRelease(AdminTables.UploadRelease):
    url = "horizon:dc_admin:dc_software_management:dc_releaseupload"


class ReleasesTable(AdminTables.ReleasesTable):
    index_url = 'horizon:dc_admin:dc_software_management:index'
    release_id = tables.Column('release_id',
                               link="horizon:dc_admin:dc_software_management:"
                                    "dc_releasedetail",
                               verbose_name=_('Release'))

    class Meta(object):
        name = "dc_releases"
        multi_select = True
        row_class = AdminTables.UpdateReleaseRow
        status_columns = ['state']
        row_actions = (
            AdminTables.DeployPrecheck,
            AdminTables.DeployStart,
            AdminTables.DeployActivate,
            AdminTables.DeleteRelease,
            AdminTables.DeployDelete
        )
        table_actions = (
            AdminTables.ReleaseFilterAction,
            UploadRelease,
            AdminTables.DeleteRelease
        )
        verbose_name = _("Releases")
        hidden_title = False

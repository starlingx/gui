#
# Copyright (c) 2018-2022 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import tables

from starlingx_dashboard.dashboards.admin.software_management import tables \
    as AdminTables

LOG = logging.getLogger(__name__)


# Patching
class UploadPatch(AdminTables.UploadPatch):
    url = "horizon:dc_admin:dc_software_management:dc_patchupload"


class PatchesTable(AdminTables.PatchesTable):
    index_url = 'horizon:dc_admin:dc_software_management:index'
    patch_id = tables.Column('patch_id',
                             link="horizon:dc_admin:dc_software_management:"
                                  "dc_patchdetail",
                             verbose_name=_('Patch ID'))

    class Meta(object):
        name = "dc_patches"
        multi_select = True
        row_class = AdminTables.UpdatePatchRow
        status_columns = ['patchstate']
        row_actions = (AdminTables.ApplyPatch, AdminTables.RemovePatch,
                       AdminTables.DeletePatch)
        table_actions = (
            AdminTables.PatchFilterAction, UploadPatch, AdminTables.ApplyPatch,
            AdminTables.RemovePatch, AdminTables.DeletePatch)
        verbose_name = _("Patches")
        hidden_title = False

#
# Copyright (c) 2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import tables


LOG = logging.getLogger(__name__)


class UpdateFilesystems(tables.LinkAction):
    name = "updatefilesystems"
    verbose_name = _("Update Filesystems")
    url = "horizon:admin:inventory:updatefilesystems"
    classes = ("ajax-modal", "btn-edit")

    def get_link_url(self, datum=None):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id,))

    def allowed(self, request, datum):
        return True


class FilesystemsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))

    size = tables.Column('size', verbose_name=_('Size (GiB)'))

    def get_object_id(self, datum):
        return str(datum.uuid)

    class Meta(object):
        name = "filesystems"
        verbose_name = _("Filesystems")
        multi_select = False
        table_actions = (UpdateFilesystems,)

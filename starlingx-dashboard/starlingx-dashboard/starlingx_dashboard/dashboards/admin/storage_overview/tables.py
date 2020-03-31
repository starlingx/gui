#
# Copyright (c) 2016-2020 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.utils.translation import ugettext_lazy as _
from horizon import tables


class MonitorsTable(tables.DataTable):
    host = tables.Column('host',
                         verbose_name=_('Host'))
    rank = tables.Column('rank',
                         verbose_name=_('Rank'))

    def get_object_id(self, obj):
        return obj.host  # hostname is always unique

    class Meta(object):
        name = "monitors"
        verbose_name = _("Monitors")
        multi_select = False
        hidden_title = False
        footer = False


class OSDsTable(tables.DataTable):
    host = tables.Column('host',
                         verbose_name=_('Host'))
    name = tables.Column('name',
                         verbose_name=_('Name'))
    status = tables.Column('status',
                           verbose_name=_('Status'))

    def get_object_id(self, obj):
        return obj.id

    class Meta(object):
        name = "osds"
        verbose_name = _("OSDs")
        multi_select = False
        hidden_title = False
        footer = False

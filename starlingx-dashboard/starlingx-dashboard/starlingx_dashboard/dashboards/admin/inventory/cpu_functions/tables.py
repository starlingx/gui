#
# Copyright (c) 2013-2021 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django import template
from django.urls import reverse  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from starlingx_dashboard.dashboards.admin.inventory.cpu_functions \
    import utils as cpufunctions_utils

LOG = logging.getLogger(__name__)


class EditCpuFunctions(tables.LinkAction):
    name = "editCpuFunctions"
    verbose_name = _("Edit CPU Assignments")
    url = "horizon:admin:inventory:editcpufunctions"
    classes = ("ajax-modal", "btn-create")

    def get_link_url(self, datum=None):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id,))

    def allowed(self, request, cpufunction=None):
        host = self.table.kwargs['host']
        allowed = host._administrative == 'locked' and \
            'worker' in host.subfunctions
        return allowed


def get_function_name(datum):
    if datum.allocated_function in cpufunctions_utils.CPU_TYPE_FORMATS:
        return cpufunctions_utils.CPU_TYPE_FORMATS[datum.allocated_function]
    return "unknown({})".format(datum.allocated_function)


def get_socket_cores(datum):
    template_name = 'admin/inventory/cpu_functions/' \
                    '_cpufunction_processorcores.html'
    context = {"cpufunction": datum}
    return template.loader.render_to_string(template_name, context)


class CpuFunctionsTable(tables.DataTable):
    allocated_function = tables.Column(get_function_name,
                                       verbose_name=_('Function'))

    socket_cores = tables.Column(get_socket_cores,
                                 verbose_name=_('Processor Logical Cores'))

    def get_object_id(self, datum):
        return str(datum.allocated_function)

    class Meta(object):
        name = "cpufunctions"
        verbose_name = _("CPU Assignments")
        multi_select = False
        table_actions = (EditCpuFunctions,)
        row_actions = ()
        hidden_title = False
        footer = False

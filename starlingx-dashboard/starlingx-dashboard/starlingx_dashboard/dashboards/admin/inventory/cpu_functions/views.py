#
# Copyright (c) 2013-2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

import utils as icpu_utils

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms

from starlingx_dashboard.api import sysinv
from starlingx_dashboard.dashboards.admin.inventory.cpu_functions.forms \
    import AddCpuProfile
from starlingx_dashboard.dashboards.admin.inventory.cpu_functions.forms \
    import UpdateCpuFunctions
from starlingx_dashboard.dashboards.admin.inventory.cpu_functions \
    import utils as cpufunctions_utils

LOG = logging.getLogger(__name__)


class UpdateCpuFunctionsView(forms.ModalFormView):
    form_class = UpdateCpuFunctions
    template_name = 'admin/inventory/cpu_functions/update.html'
    context_object_name = 'cpufunctions'
    success_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            host_id = self.kwargs['host_id']
            try:
                host = sysinv.host_get(self.request, host_id)
                host.nodes = sysinv.host_node_list(self.request, host.uuid)
                host.cpus = sysinv.host_cpu_list(self.request, host.uuid)
                host.labels = sysinv.host_label_list(self.request, host.uuid)
                icpu_utils.restructure_host_cpu_data(host)
                self._object = host
                self._object.host_id = host_id
            except Exception as e:
                LOG.exception(e)
                redirect = reverse("horizon:project:networks:detail",
                                   args=(host_id))
                msg = _('Unable to retrieve port details')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_context_data(self, **kwargs):
        context = \
            super(UpdateCpuFunctionsView, self).get_context_data(**kwargs)
        host = self._get_object()
        context['host_id'] = host.host_id
        return context

    def get_physical_core_count(self, host, cpufunc, socket):
        value = cpufunc.socket_cores_number.get(socket, 0)
        if host.hyperthreading.lower() == "yes":
            value = value / 2
        return value

    def get_initial(self):
        host = self._get_object()

        cpu_assignments = {}
        numa_count = len(host.nodes)

        for function in icpu_utils.CPU_TYPE_LIST:
            core_counts = [0] * numa_count
            cpu_assignments.update({function: core_counts})

        for cpu in host.cpus:
            # We only want physical cores
            if cpu.thread != 0:
                continue
            cpu_assignments[cpu.allocated_function][cpu.numa_node] += 1

        formatted_data = {
            'host': host,
            'host_id': host.host_id,
            'cpu_assignments': cpu_assignments
        }

        return formatted_data


class AddCpuProfileView(forms.ModalFormView):
    form_class = AddCpuProfile
    template_name = 'admin/inventory/cpu_functions/createprofile.html'
    success_url = 'horizon:admin:inventory:detail'
    failure_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def get_failure_url(self):
        return reverse(self.failure_url,
                       args=(self.kwargs['host_id'],))

    def get_myhost_data(self):
        if not hasattr(self, "_host"):
            host_id = self.kwargs['host_id']
            try:
                host = sysinv.host_get(self.request, host_id)
                host.nodes = sysinv.host_node_list(self.request, host.uuid)
                host.cpus = sysinv.host_cpu_list(self.request, host.uuid)
                icpu_utils.restructure_host_cpu_data(host)
            except Exception:
                redirect = reverse('horizon:admin:inventory:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'host "%s".') % host_id,
                                  redirect=redirect)
            self._host = host
        return self._host

    def get_context_data(self, **kwargs):
        context = super(AddCpuProfileView, self).get_context_data(**kwargs)
        context['host_id'] = self.kwargs['host_id']
        context['host'] = self.get_myhost_data()
        context['cpu_formats'] = cpufunctions_utils.CPU_TYPE_FORMATS
        return context

    def get_initial(self):
        initial = super(AddCpuProfileView, self).get_initial()
        initial['host_id'] = self.kwargs['host_id']
        return initial

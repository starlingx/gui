#
# Copyright (c) 2013-2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

from cgtsclient import exc
from django.core.urlresolvers import reverse  # noqa
from django import shortcuts
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from starlingx_dashboard.api import sysinv
from starlingx_dashboard.dashboards.admin.inventory.cpu_functions \
    import utils as cpu_utils
from starlingx_dashboard.horizon.forms.fields import DynamicIntegerField

LOG = logging.getLogger(__name__)

FUNCTION_LABEL = _(
    "------------------------ Function ------------------------")


class UpdateCpuFunctions(forms.SelfHandlingForm):

    failure_url = 'horizon:admin:inventory:detail'

    def __init__(self, *args, **kwargs):
        super(UpdateCpuFunctions, self).__init__(*args, **kwargs)

        self.host = kwargs['initial']['host']
        self.cpu_assignments = kwargs['initial']['cpu_assignments']

        numa_count = len(self.host.nodes)

        default_label_text = _("# of %(type)s Cores on Processor %(numa)s:")
        default_help_text = _(
            "Processor %(numa)s has %(count)s physical cores.")
        shared_help_text = _(
            "Each processor can have at most one shared core.")

        self.field_matrix = dict(cpu_utils.CPU_TYPE_MATRIX)

        if 'worker' not in self.host.subfunctions:
            # Ignore worker-only cpu types
            self.field_matrix = dict(
                field for field in self.field_matrix.items()
                if not field[1]['worker-only'])
        else:
            # Update the help text and max value for the shared cpu type
            self.field_matrix[cpu_utils.SHARED_CPU_TYPE].update({
                "help_text": shared_help_text,
                "max_value": 1})

        for cpu_type, cpu_type_properties in self.field_matrix.items():
            cpu_format = cpu_type_properties['format']
            index = "%s_function_label" % cpu_type

            # Add function header label
            self.fields[index] = \
                forms.CharField(
                    label=FUNCTION_LABEL,
                    initial=cpu_format,
                    required=False,
                    widget=forms.TextInput(attrs={'readonly': 'readonly'}))

            for numa_node in range(numa_count):
                avail_socket_cores = self.host.physical_cores.get(numa_node, 0)
                label_text = cpu_type_properties.get(
                    "label", default_label_text % {'type': cpu_format,
                                                   'numa': numa_node})
                max_value = cpu_type_properties.get(
                    "max_value", avail_socket_cores)
                help_text = cpu_type_properties.get(
                    "help_text", default_help_text % {
                        'numa': numa_node, 'count': avail_socket_cores})

                index = "%s_%s" % (cpu_type, numa_node)
                core_count = self.cpu_assignments[cpu_type][numa_node]

                # Add input field with appropriate values
                self.fields[index] = \
                    DynamicIntegerField(
                        label=label_text,
                        min_value=0,
                        max_value=max_value,
                        help_text=help_text,
                        initial=core_count,
                        required=False)

    def clean(self):
        cleaned_data = super(UpdateCpuFunctions, self).clean()

        numa_count = len(self.host.nodes)

        updated_cpu_assignments = {}

        try:
            for cpu_type in self.field_matrix.keys():
                # Build up the updated_cpu_assignments structure
                core_counts = [0] * numa_count
                updated_cpu_assignments.update({cpu_type: core_counts})

                # Add the data for each input
                for numa_node in range(numa_count):
                    index = "%s_%s" % (cpu_type, numa_node)
                    if cleaned_data[index] is None:
                        raise forms.ValidationError(_("Invalid entry."))
                    updated_cpu_assignments[cpu_type][numa_node] = \
                        str(cleaned_data[index])
        except Exception as e:
            LOG.error(e)
            raise forms.ValidationError(_("Invalid entry."))

        return updated_cpu_assignments

    def handle(self, request, data):
        host_id = self.host.uuid
        try:
            sysinv.host_cpus_modify(request, host_id, data)
            msg = _('CPU Assignments were successfully updated.')
            LOG.debug(msg)
            messages.success(request, msg)
            return self.host.cpus
        except exc.ClientException as ce:
            # Display REST API error message on UI
            messages.error(request, ce)
            LOG.error(ce)

            # Redirect to failure pg
            redirect = reverse(self.failure_url, args=[host_id])
            return shortcuts.redirect(redirect)
        except Exception as e:
            LOG.exception(e)
            msg = _('Failed to update CPU Assignments.')
            LOG.info(msg)
            redirect = reverse(self.failure_url, args=[host_id])
            exceptions.handle(request, msg, redirect=redirect)


class AddCpuProfile(forms.SelfHandlingForm):
    host_id = forms.CharField(widget=forms.widgets.HiddenInput)
    profilename = forms.CharField(label=_("Cpu Profile Name"),
                                  required=True)

    failure_url = 'horizon:admin:inventory:detail'

    def __init__(self, *args, **kwargs):
        super(AddCpuProfile, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(AddCpuProfile, self).clean()
        # host_id = cleaned_data.get('host_id')
        return cleaned_data

    def handle(self, request, data):

        cpuProfileName = data['profilename']
        try:
            cpuProfile = sysinv.host_cpuprofile_create(request, **data)
            msg = _(
                'Cpu Profile "%s" was successfully created.') % cpuProfileName
            LOG.debug(msg)
            messages.success(request, msg)
            return cpuProfile
        except exc.ClientException as ce:
            # Display REST API error message on UI
            messages.error(request, ce)
            LOG.error(ce)

            # Redirect to failure pg
            redirect = reverse(self.failure_url, args=[data['host_id']])
            return shortcuts.redirect(redirect)
        except Exception:
            msg = _('Failed to create cpu profile "%s".') % cpuProfileName
            LOG.info(msg)
            redirect = reverse(self.failure_url,
                               args=[data['host_id']])
            exceptions.handle(request, msg, redirect=redirect)

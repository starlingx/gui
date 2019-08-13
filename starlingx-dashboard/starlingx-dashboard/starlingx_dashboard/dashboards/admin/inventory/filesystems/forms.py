#
# Copyright (c) 2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms

from starlingx_dashboard import api as stx_api

LOG = logging.getLogger(__name__)


class UpdateFilesystems(forms.SelfHandlingForm):

    host_id = forms.CharField(label=_("host_id"),
                              required=False,
                              widget=forms.widgets.HiddenInput)

    host_uuid = forms.CharField(label=_("host_uuid"),
                                required=False,
                                widget=forms.widgets.HiddenInput)

    backup = forms.IntegerField(
        label=_("Backup Storage (GiB)"),
        required=False,
        help_text=_("Backup storage space in gibibytes."),
        min_value=0)

    docker = forms.IntegerField(
        label=_("Docker Storage (GiB)"),
        required=True,
        help_text=_("Docker storage space in gibibytes."),
        min_value=0)

    kubelet = forms.IntegerField(
        label=_("Kubelet Storage (GiB)"),
        required=True,
        help_text=_("Kubelet storage space in gibibytes."),
        min_value=0)

    scratch = forms.IntegerField(
        label=_("Scratch Storage (GiB)"),
        required=True,
        help_text=_("Scratch storage space in gibibytes."),
        min_value=0)

    failure_url = 'horizon:admin:inventory:detail'
    failure_message = 'Failed to update host filesystems configuration.'

    def __init__(self, request, *args, **kwargs):
        super(UpdateFilesystems, self).__init__(request, *args, **kwargs)

        # The backup fs is only used on controller nodes. Removed from form if
        # its not in the list.
        if not kwargs['initial'].get('backup'):
            del self.fields['backup']

    def clean(self):
        cleaned_data = super(UpdateFilesystems, self).clean()
        return cleaned_data

    def handle(self, request, data):
        host_uuid = data['host_uuid']
        data.pop('host_uuid')
        data.pop('host_id')

        new_data = {k.replace("_", "-"): v for k, v in data.items()}

        try:
            fs_list = stx_api.sysinv.host_filesystems_list(
                self.request, host_uuid)

            fs_data = {fs.name: fs.size for fs in fs_list}

            for k, v in fs_data.items():
                if new_data.get(k, None) == v:
                    del new_data[k]

            if new_data:
                stx_api.sysinv.host_filesystems_update(request,
                                                       host_uuid,
                                                       **new_data)
            return True
        except Exception as exc:
            msg = _('Failed to update host filesystems (%(e)s).') \
                % ({'e': exc})
            LOG.info(msg)
            redirect = reverse(self.failure_url, args=[host_uuid])
            exceptions.handle(request, msg, redirect=redirect)

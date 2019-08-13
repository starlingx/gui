#
# Copyright (c) 2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms

from starlingx_dashboard import api as stx_api

from starlingx_dashboard.dashboards.admin.inventory.filesystems.forms \
    import UpdateFilesystems

LOG = logging.getLogger(__name__)


class UpdateFilesystemsView(forms.ModalFormView):
    form_class = UpdateFilesystems
    template_name = 'admin/inventory/filesystems/update_filesystems_table.html'
    success_url = 'horizon:admin:inventory:detail'
    failure_url = 'horizon:admin:inventory:detail'
    context_object_name = "filesystems"

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def get_failure_url(self):
        return reverse(self.failure_url,
                       args=(self.kwargs['host_id'],))

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            host_id = self.kwargs['host_id']

            try:
                host = stx_api.sysinv.host_get(self.request, host_id)
                host.filesystems = stx_api.sysinv.host_filesystems_list(
                    self.request, host.uuid)
                host.nodes = \
                    stx_api.sysinv.host_node_list(self.request, host.uuid)
                self._object = host
                self._object.host_id = host_id
            except Exception as e:
                LOG.exception(e)
                redirect = reverse(self.failure_url,
                                   args=host_id)
                msg = _('Unable to retrieve host filesystems details')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_context_data(self, **kwargs):

        context = super(UpdateFilesystemsView, self).get_context_data(**kwargs)
        host = self._get_object()
        context['host_id'] = host.host_id

        return context

    def get_initial(self):

        host = self._get_object()
        fs_form_data = \
            {fs.name.replace("-", "_"): fs.size for fs in host.filesystems}
        fs_form_data.update({'host_uuid': host.uuid})
        fs_form_data.update({'host_id': host.id})

        return fs_form_data

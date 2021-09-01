#
# Copyright (c) 2013-2015, 2017-2021 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tabs
from horizon.utils import memoized
from horizon import views

from starlingx_dashboard.api import sysinv
from starlingx_dashboard.dashboards.admin.inventory.storages.forms import \
    AddLocalVolumeGroup
from starlingx_dashboard.dashboards.admin.inventory.storages.forms import \
    AddPhysicalVolume
from starlingx_dashboard.dashboards.admin.inventory.storages.forms import \
    AddStorageVolume
from starlingx_dashboard.dashboards.admin.inventory.storages.forms import \
    CreatePartition
from starlingx_dashboard.dashboards.admin.inventory.storages.forms import \
    EditPartition
from starlingx_dashboard.dashboards.admin.inventory.storages.forms import \
    EditStorageVolume
from starlingx_dashboard.dashboards.admin.inventory.storages.tabs \
    import LocalVolumeGroupDetailTabs

LOG = logging.getLogger(__name__)


class AddStorageVolumeView(forms.ModalFormView):
    form_class = AddStorageVolume
    template_name = 'admin/inventory/storages/createstoragevolume.html'
    success_url = 'horizon:admin:inventory:detail'
    failure_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def get_failure_url(self):
        return reverse(self.failure_url,
                       args=(self.kwargs['host_id'],))

    def get_context_data(self, **kwargs):
        context = super(AddStorageVolumeView, self).get_context_data(**kwargs)
        context['host_id'] = self.kwargs['host_id']
        return context

    def get_initial(self):
        initial = super(AddStorageVolumeView, self).get_initial()
        initial['host_id'] = self.kwargs['host_id']
        try:
            host = sysinv.host_get(self.request, initial['host_id'])
        except Exception:
            exceptions.handle(self.request, _('Unable to retrieve host.'))
        initial['ihost_uuid'] = host.uuid
        initial['hostname'] = host.hostname
        return initial


class EditStorageVolumeView(forms.ModalFormView):
    form_class = EditStorageVolume
    template_name = 'admin/inventory/storages/editstoragevolume.html'
    success_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            stor_uuid = self.kwargs['stor_uuid']
            host_id = self.kwargs['host_id']
            LOG.debug("stor_id=%s kwargs=%s",
                      stor_uuid, self.kwargs)
            try:
                self._object = sysinv.host_stor_get(self.request,
                                                    stor_uuid)
                self._object.host_id = host_id
            except Exception:
                redirect = reverse("horizon:admin:inventory:detail",
                                   args=(self.kwargs['host_id'],))
                msg = _('Unable to retrieve stor details')
                exceptions.handle(self.request, msg, redirect=redirect)

        return self._object

    def get_context_data(self, **kwargs):
        context = super(EditStorageVolumeView, self).get_context_data(**kwargs)
        stor = self._get_object()
        context['stor_uuid'] = stor.uuid
        context['host_id'] = stor.host_id
        return context

    def get_initial(self):
        stor = self._get_object()
        return {'id': stor.uuid,
                'uuid': stor.uuid,
                'host_uuid': stor.ihost_uuid,
                'journal_location': stor.journal_location,
                'journal_size_mib': stor.journal_size_mib}


class AddLocalVolumeGroupView(forms.ModalFormView):
    form_class = AddLocalVolumeGroup
    template_name = 'admin/inventory/storages/createlocalvolumegroup.html'
    success_url = 'horizon:admin:inventory:detail'
    failure_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def get_failure_url(self):
        return reverse(self.failure_url,
                       args=(self.kwargs['host_id'],))

    def get_context_data(self, **kwargs):
        context = super(AddLocalVolumeGroupView, self) \
            .get_context_data(**kwargs)
        context['host_id'] = self.kwargs['host_id']
        return context

    def get_initial(self):
        initial = super(AddLocalVolumeGroupView, self).get_initial()
        initial['host_id'] = self.kwargs['host_id']
        try:
            host = sysinv.host_get(self.request, initial['host_id'])
        except Exception:
            exceptions.handle(self.request, _('Unable to retrieve host.'))
        initial['ihost_uuid'] = host.uuid
        initial['hostname'] = host.hostname
        return initial


class AddPhysicalVolumeView(forms.ModalFormView):
    form_class = AddPhysicalVolume
    template_name = 'admin/inventory/storages/createphysicalvolume.html'
    success_url = 'horizon:admin:inventory:detail'
    failure_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def get_failure_url(self):
        return reverse(self.failure_url,
                       args=(self.kwargs['host_id'],))

    def get_context_data(self, **kwargs):
        context = super(AddPhysicalVolumeView, self).get_context_data(**kwargs)
        context['host_id'] = self.kwargs['host_id']
        return context

    def get_initial(self):
        initial = super(AddPhysicalVolumeView, self).get_initial()
        initial['host_id'] = self.kwargs['host_id']
        try:
            host = sysinv.host_get(self.request, initial['host_id'])
        except Exception:
            exceptions.handle(self.request, _('Unable to retrieve host.'))
        initial['ihost_uuid'] = host.uuid
        initial['hostname'] = host.hostname
        return initial


class DetailPhysicalVolumeView(views.HorizonTemplateView):
    template_name = 'admin/inventory/_detail_physical_volume.html'
    page_title = "{{ pv.lvm_pv_name }}"

    def get_context_data(self, **kwargs):
        context = super(DetailPhysicalVolumeView, self)\
            .get_context_data(**kwargs)
        pv = self.get_data()

        hostname = self.get_hostname(pv.ihost_uuid)
        host_nav = hostname or "Unprovisioned Node"
        breadcrumb = [
            (host_nav, reverse('horizon:admin:inventory:detail',
                               args=(pv.ihost_uuid,))),
            (_("Physical Volumes"), None)
        ]
        context["custom_breadcrumb"] = breadcrumb

        context["pv"] = pv
        return context

    @memoized.memoized_method
    def get_hostname(self, host_uuid):
        try:
            host = sysinv.host_get(self.request, host_uuid)
        except Exception:
            host = {}
            msg = _('Unable to retrieve hostname details.')
            exceptions.handle(self.request, msg)
        return host.hostname

    def get_data(self):
        if not hasattr(self, "_pv"):
            pv_id = self.kwargs['pv_id']
            try:
                pv = sysinv.host_pv_get(self.request, pv_id)
            except Exception:
                redirect = reverse('horizon:admin:inventory:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'physical volume "%s".') % pv_id,
                                  redirect=redirect)

            self._pv = pv
        return self._pv


class DetailLocalVolumeGroupView(tabs.TabbedTableView):
    tab_group_class = LocalVolumeGroupDetailTabs
    template_name = 'admin/inventory/_detail_local_volume_group.html'
    page_title = "{{ lvg.lvm_vg_name}}"

    def get_context_data(self, **kwargs):
        context = super(DetailLocalVolumeGroupView, self)\
            .get_context_data(**kwargs)
        lvg = self.get_data()

        hostname = self.get_hostname(lvg.ihost_uuid)
        host_nav = hostname or "Unprovisioned Node"
        breadcrumb = [
            (host_nav, reverse('horizon:admin:inventory:detail',
                               args=(lvg.ihost_uuid,))),
            (_("Local Volume Groups"), None)
        ]
        context["custom_breadcrumb"] = breadcrumb

        context["lvg"] = lvg
        return context

    def get_data(self):
        if not hasattr(self, "_lvg"):
            lvg_id = self.kwargs['lvg_id']
            try:
                lvg = sysinv.host_lvg_get(self.request, lvg_id)
            except Exception:
                redirect = reverse('horizon:admin:inventory:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'local volume group "%s".') % lvg_id,
                                  redirect=redirect)

            self._lvg = lvg
        return self._lvg

    @memoized.memoized_method
    def get_hostname(self, host_uuid):
        try:
            host = sysinv.host_get(self.request, host_uuid)
        except Exception:
            host = {}
            msg = _('Unable to retrieve hostname details.')
            exceptions.handle(self.request, msg)
        return host.hostname

    def get_tabs(self, request, *args, **kwargs):
        lvg = self.get_data()
        return self.tab_group_class(request, lvg=lvg, **kwargs)


class CreatePartitionView(forms.ModalFormView):
    form_class = CreatePartition
    template_name = 'admin/inventory/storages/createpartition.html'
    success_url = 'horizon:admin:inventory:detail'
    failure_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def get_failure_url(self):
        return reverse(self.failure_url,
                       args=(self.kwargs['host_id'],))

    def get_context_data(self, **kwargs):
        context = super(CreatePartitionView, self).get_context_data(**kwargs)
        context['host_id'] = self.kwargs['host_id']
        return context

    def get_initial(self):
        initial = super(CreatePartitionView, self).get_initial()
        initial['host_id'] = self.kwargs['host_id']
        try:
            host = sysinv.host_get(self.request, initial['host_id'])
        except Exception:
            exceptions.handle(self.request, _('Unable to retrieve host.'))
        initial['ihost_uuid'] = host.uuid
        initial['hostname'] = host.hostname
        return initial


class EditPartitionView(forms.ModalFormView):
    form_class = EditPartition
    template_name = 'admin/inventory/storages/editpartition.html'
    success_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            partition_uuid = self.kwargs['partition_uuid']
            host_id = self.kwargs['host_id']
            LOG.debug("partition_id=%s kwargs=%s",
                      partition_uuid, self.kwargs)
            try:
                self._object = sysinv.host_disk_partition_get(
                    self.request,
                    partition_uuid)
                self._object.host_id = host_id
            except Exception:
                redirect = reverse("horizon:admin:inventory:detail",
                                   args=(self.kwargs['host_id'],))
                msg = _('Unable to retrieve partition details')
                exceptions.handle(self.request, msg, redirect=redirect)

        return self._object

    def get_context_data(self, **kwargs):
        context = super(EditPartitionView, self).get_context_data(**kwargs)
        partition = self._get_object()
        context['partition_uuid'] = partition.uuid
        context['host_id'] = partition.host_id
        return context

    def get_initial(self):
        partition = self._get_object()
        return {'id': partition.uuid,
                'uuid': partition.uuid,
                'host_uuid': partition.ihost_uuid,
                'size_gib': partition.size_gib}

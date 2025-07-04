#
# Copyright (c) 2013-2023 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized

from starlingx_dashboard import api as stx_api
from starlingx_dashboard.dashboards.admin.inventory.interfaces.address import \
    tables as address_tables
from starlingx_dashboard.dashboards.admin.inventory.interfaces.forms import \
    AddInterface
from starlingx_dashboard.dashboards.admin.inventory.interfaces.forms import \
    UpdateInterface
from starlingx_dashboard.dashboards.admin.inventory.interfaces.route import \
    tables as route_tables

LOG = logging.getLogger(__name__)


def get_port_data(request, host_id, interface=None):
    port_data = []
    show_all_ports = True

    try:
        if not interface:
            # Create case, host id is not UUID. Need to get the UUID in order
            # to retrieve the ports for this host
            host = stx_api.sysinv.host_get(request, host_id)
            host_id = host.uuid
        else:
            if not interface.uses:
                show_all_ports = False

        port_list = \
            stx_api.sysinv.host_port_list(request, host_id)

        if show_all_ports:
            # This is either a create or edit non-default interface
            # operation. Get the list of available ports and their
            # neighbours
            neighbour_list = \
                stx_api.sysinv.host_lldpneighbour_list(request, host_id)
            interface_list = stx_api.sysinv.host_interface_list(request,
                                                                host_id)

            for p in port_list:
                port_info = "%s (%s, %s, " % (p.get_port_display_name(),
                                              p.mac, p.pciaddr)
                interface_name = ''
                for i in interface_list:
                    if p.interface_uuid == i.uuid:
                        interface_name = i.ifname

                if interface_name:
                    port_info += interface_name + ")"
                else:
                    port_info += _("none") + ")"

                if p.bootp:
                    port_info += " - bootif"

                neighbour_info = []
                for n in neighbour_list:
                    if p.uuid == n.port_uuid:
                        if n.port_description:
                            neighbour = "%s (%s)" % (
                                n.port_identifier, n.port_description)
                        else:
                            neighbour = "%s" % n.port_identifier
                        neighbour_info.append(neighbour)
                neighbour_info.sort()
                port_data_item = port_info, neighbour_info
                port_data.append(port_data_item)
        else:
            # Edit default-interface operation
            for p in port_list:
                # Since the port->default interface mapping is now strictly
                # 1:1, the below condition can only be met at most once for
                # the available ports
                if p.interface_uuid == interface.uuid:
                    port_info = "%s (%s, %s, %s)" % (
                        p.get_port_display_name(), p.mac, p.pciaddr,
                        interface.ifname)

                    if p.bootp:
                        port_info += " - bootif"
                    # Retrieve the neighbours for the port
                    neighbours = \
                        stx_api.sysinv.port_lldpneighbour_list(request, p.uuid)
                    neighbour_info = []
                    if neighbours:
                        for n in neighbours:
                            if n.port_description:
                                neighbour = "%s (%s)" % (
                                    n.port_identifier, n.port_description)
                            else:
                                neighbour = "%s\n" % n.port_identifier
                            neighbour_info.append(neighbour)
                    neighbour_info.sort()
                    port_data_item = port_info, neighbour_info
                    port_data.append(port_data_item)
    except Exception:
        redirect = reverse('horizon:admin:inventory:index')
        exceptions.handle(request,
                          _('Unable to retrieve port info details for host '
                            '"%s".') % host_id, redirect=redirect)

    return port_data


class AddInterfaceView(forms.ModalFormView):
    form_class = AddInterface
    template_name = 'admin/inventory/interfaces/create.html'
    success_url = 'horizon:admin:inventory:detail'
    failure_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def get_failure_url(self):
        return reverse(self.failure_url,
                       args=(self.kwargs['host_id'],))

    def get_context_data(self, **kwargs):
        context = super(AddInterfaceView, self).get_context_data(**kwargs)
        context['host_id'] = self.kwargs['host_id']
        context['ports'] = get_port_data(self.request, self.kwargs['host_id'])
        return context

    def get_initial(self):
        initial = super(AddInterfaceView, self).get_initial()
        initial['host_id'] = self.kwargs['host_id']
        try:
            host = stx_api.sysinv.host_get(self.request, initial['host_id'])
        except Exception:
            exceptions.handle(self.request, _('Unable to retrieve host.'))
        initial['ihost_uuid'] = host.uuid
        initial['host'] = host

        # get SDN configuration status
        sdn_enabled = False
        try:
            sdn_enabled = stx_api.sysinv.get_sdn_enabled(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve SDN configuration.'))
        initial['sdn_enabled'] = sdn_enabled
        return initial


class UpdateView(forms.ModalFormView):
    form_class = UpdateInterface
    template_name = 'admin/inventory/interfaces/update.html'
    success_url = 'horizon:admin:inventory:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['host_id'],))

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            interface_id = self.kwargs['interface_id']
            host_id = self.kwargs['host_id']
            try:
                self._object = stx_api.sysinv.host_interface_get(self.request,
                                                                 interface_id)
                self._object.host_id = host_id

            except Exception:
                redirect = reverse("horizon:project:networks:detail",
                                   args=(self.kwargs['host_id'],))
                msg = _('Unable to retrieve interface details')
                exceptions.handle(self.request, msg, redirect=redirect)

        return self._object

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        interface = self._get_object()
        context['interface_id'] = interface.uuid
        context['host_id'] = interface.host_id
        ports = get_port_data(self.request, interface.ihost_uuid, interface)
        if ports:
            context['ports'] = ports
        return context

    def get_initial(self):
        interface = self._get_object()

        try:
            host = stx_api.sysinv.host_get(self.request, interface.host_id)
        except Exception:
            exceptions.handle(self.request, _('Unable to retrieve host.'))

        # get SDN configuration status
        sdn_enabled = False
        try:
            sdn_enabled = stx_api.sysinv.get_sdn_enabled(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve SDN configuration.'))

        return {'id': interface.uuid,
                'host_id': interface.host_id,
                'host': host,
                'ihost_uuid': interface.ihost_uuid,
                'ifname': interface.ifname,
                'iftype': interface.iftype,
                'aemode': interface.aemode,
                'txhashpolicy': interface.txhashpolicy,
                'primary_reselect': interface.primary_reselect,
                # 'ports': interface.ports,
                # 'uses': interface.uses,
                'ifclass': interface.ifclass,
                'sriov_numvfs': interface.sriov_numvfs,
                'sriov_vf_driver': interface.sriov_vf_driver,
                'imtu': interface.imtu,
                'max_tx_rate': interface.max_tx_rate,
                'max_rx_rate': interface.max_rx_rate,
                'ipv4_mode': getattr(interface, 'ipv4_mode', 'disabled'),
                'ipv4_pool': getattr(interface, 'ipv4_pool', None),
                'ipv6_mode': getattr(interface, 'ipv6_mode', 'disabled'),
                'ipv6_pool': getattr(interface, 'ipv6_pool', None),
                'sdn_enabled': sdn_enabled}


class DetailView(tables.MultiTableView):
    table_classes = (address_tables.AddressTable,
                     route_tables.RouteTable)
    template_name = 'admin/inventory/interfaces/detail.html'
    failure_url = reverse_lazy('horizon:admin:inventory:detail')
    page_title = "{{ interface.ifname }}"

    def get_addresses_data(self):
        try:
            interface_id = self.kwargs['interface_id']
            addresses = stx_api.sysinv.address_list_by_interface(
                self.request, interface_id=interface_id)
            addresses.sort(key=lambda f: (f.address, f.prefix))
        except Exception:
            addresses = []
            msg = _('Address list can not be retrieved.')
            exceptions.handle(self.request, msg)
        return addresses

    def get_routes_data(self):
        try:
            interface_id = self.kwargs['interface_id']
            routes = stx_api.sysinv.route_list_by_interface(
                self.request, interface_id=interface_id)
            routes.sort(key=lambda f: (f.network, f.prefix))
        except Exception:
            routes = []
            msg = _('Route list can not be retrieved.')
            exceptions.handle(self.request, msg)
        return routes

    def _get_address_pools(self):
        pools = stx_api.sysinv.address_pool_list(self.request)
        return {p.uuid: p for p in pools}

    def _add_pool_names(self, interface):
        pools = self._get_address_pools()
        if getattr(interface, 'ipv4_mode', '') == 'pool':
            interface.ipv4_pool_name = pools[interface.ipv4_pool].name
        if getattr(interface, 'ipv6_mode', '') == 'pool':
            interface.ipv6_pool_name = pools[interface.ipv6_pool].name
        return interface

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            interface_id = self.kwargs['interface_id']
            host_id = self.kwargs['host_id']
            try:
                self._object = stx_api.sysinv.host_interface_get(self.request,
                                                                 interface_id)
                self._object.host_id = host_id
                self._object = self._add_pool_names(self._object)
            except Exception:
                redirect = reverse("horizon:admin:inventory:detail",
                                   args=(self.kwargs['host_id'],))
                msg = _('Unable to retrieve interface details')
                exceptions.handle(self.request, msg, redirect=redirect)

        return self._object

    @memoized.memoized_method
    def get_hostname(self, host_uuid):
        try:
            host = stx_api.sysinv.host_get(self.request, host_uuid)
        except Exception:
            host = {}
            msg = _('Unable to retrieve hostname details.')
            exceptions.handle(self.request, msg)
        return host.hostname

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        interface = self._get_object()

        hostname = self.get_hostname(interface.host_id)
        host_nav = hostname or "Unprovisioned Node"
        breadcrumb = [
            (host_nav, reverse('horizon:admin:inventory:detail',
                               args=(interface.host_id,))),
            (_("Interfaces"), None)
        ]
        context["custom_breadcrumb"] = breadcrumb

        context['interface_id'] = interface.uuid
        context['host_id'] = interface.host_id
        context['interface'] = interface
        return context

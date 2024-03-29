#
# Copyright (c) 2013-2022 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.template import defaultfilters as filters
from django.urls import reverse  # noqa
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables

from starlingx_dashboard import api as stx_api
import sysinv.common.constants as sysinv_const

LOG = logging.getLogger(__name__)


class DeleteInterface(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Delete Interface",
            "Delete Interfaces",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Deleted Interface",
            "Deleted Interfaces",
            count
        )

    def allowed(self, request, interface=None):
        host = self.table.kwargs['host']
        if interface.uses:
            if (stx_api.sysinv.is_system_mode_simplex(request)
                    and interface.iftype == sysinv_const.INTERFACE_TYPE_VF):
                return True
            else:
                return host._administrative == 'locked'

    def delete(self, request, interface_id):
        host_id = self.table.kwargs['host_id']
        try:
            stx_api.sysinv.host_interface_delete(request, interface_id)
        except Exception:
            msg = _('Failed to delete host %(hid)s interface %(iid)s') % {
                'hid': host_id, 'iid': interface_id}
            LOG.info(msg)
            redirect = reverse('horizon:admin:inventory:detail',
                               args=(host_id,))
            exceptions.handle(request, msg, redirect=redirect)


class CreateInterface(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Interface")
    url = "horizon:admin:inventory:addinterface"
    classes = ("ajax-modal", "btn-create")

    def get_link_url(self, datum=None):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id,))

    def allowed(self, request, datum):
        host = self.table.kwargs['host']

        is_aio_sx = stx_api.sysinv.is_system_mode_simplex(request)
        if (host._administrative != 'locked' and not is_aio_sx):
            return False

        sriov_count = 0
        for i in host.interfaces:
            if i.ifclass:
                if i.ifclass == sysinv_const.INTERFACE_CLASS_PCI_SRIOV:
                    sriov_count += 1

        if is_aio_sx and host._administrative != 'locked' and sriov_count == 0:
            return False

        return True


class EditInterface(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Interface")
    url = "horizon:admin:inventory:editinterface"
    classes = ("ajax-modal", "btn-edit")

    def get_link_url(self, interface=None):
        host_id = self.table.kwargs['host_id']
        return reverse(self.url, args=(host_id, interface.uuid))

    def allowed(self, request, datum):
        host = self.table.kwargs['host']
        intf = datum
        if (stx_api.sysinv.is_system_mode_simplex(request)
                and intf.iftype == sysinv_const.INTERFACE_TYPE_ETHERNET
                and intf.ifclass != sysinv_const.INTERFACE_CLASS_PCI_SRIOV):
            return True
        else:
            return host._administrative == 'locked'


def get_attributes(interface):
    attr_str = "MTU=%s" % interface.imtu
    if interface.iftype == 'ae':
        attr_str = "%s, AE_MODE=%s" % (attr_str, interface.aemode)
        if interface.aemode in ['balanced', '802.3ad']:
            attr_str = "%s, AE_XMIT_HASH_POLICY=%s" % (
                attr_str, interface.txhashpolicy)
        elif (interface.aemode == 'active_standby' and
                interface.primary_reselect):
            attr_str = "%s, primary_reselect=%s" % (
                attr_str, interface.primary_reselect)
    if interface.ifclass and interface.ifclass == 'data':
        attrs = [attr.strip() for attr in attr_str.split(",")]
        for a in attrs:
            if 'accelerated' in a:
                attrs.remove(a)
        attr_str = ",".join(attrs)

        if False in interface.dpdksupport:
            attr_str = "%s, accelerated=%s" % (attr_str, 'False')
        else:
            attr_str = "%s, accelerated=%s" % (attr_str, 'True')
    return attr_str


def get_ports(interface):
    port_str_list = ", ".join(interface.portNameList)
    return port_str_list


def get_port_neighbours(interface):
    return interface.portNeighbourList


def get_uses(interface):
    uses_list = ", ".join(interface.uses)
    return uses_list


def get_used_by(interface):
    used_by_list = ", ".join(interface.used_by)
    return used_by_list


def get_platform_networks(interface):
    platform_networks = ", ".join(interface.platform_network_names)
    return platform_networks


def get_data_networks(interface):
    data_networks = ", ".join(interface.data_network_names)
    return data_networks


def get_link_url(interface):
    return reverse("horizon:admin:inventory:viewinterface",
                   args=(interface.host_id, interface.uuid))


class InterfacesTable(tables.DataTable):
    ifname = tables.Column('ifname',
                           verbose_name=_('Name'),
                           link=get_link_url)

    ifclass = tables.Column('ifclass',
                            verbose_name=_('Interface Class'))

    iftype = tables.Column('iftype',
                           verbose_name=_('Type'))

    vlan_id = tables.Column('vlan_id',
                            verbose_name=_('Vlan ID'))

    ports = tables.Column(get_ports,
                          verbose_name=_('Port'))

    port_neighbours = tables.Column(get_port_neighbours,
                                    verbose_name=_('Neighbors'),
                                    wrap_list=True,
                                    filters=(filters.unordered_list,))

    uses = tables.Column(get_uses,
                         verbose_name=_('Uses'))

    used_by = tables.Column(get_used_by,
                            verbose_name=_('Used By'))

    platform_networks = tables.Column(get_platform_networks,
                                      verbose_name=_('Platform Network(s)'))

    datanetworks_csv = tables.Column(get_data_networks,
                                     verbose_name=_('Data Network(s)'))

    attributes = tables.Column(get_attributes,
                               verbose_name=_('Attributes'))

    def __init__(self, *args, **kwargs):
        super(InterfacesTable, self).__init__(*args, **kwargs)

    def get_object_id(self, datum):
        return str(datum.uuid)

    def get_object_display(self, datum):
        return datum.ifname

    class Meta(object):
        name = "interfaces"
        verbose_name = _("Interfaces")
        multi_select = False
        table_actions = (CreateInterface,)
        row_actions = (EditInterface, DeleteInterface,)

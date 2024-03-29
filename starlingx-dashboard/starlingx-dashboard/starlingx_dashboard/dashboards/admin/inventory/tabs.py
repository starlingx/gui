#
# Copyright (c) 2013-2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4


import logging

from cgtsclient import exc

from django.conf import settings
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from starlingx_dashboard import api as stx_api
from starlingx_dashboard.dashboards.admin.inventory.cpu_functions import \
    tables as cpufunctions_tables
from starlingx_dashboard.dashboards.admin.inventory.devices import \
    tables as device_tables
from starlingx_dashboard.dashboards.admin.inventory.filesystems import \
    tables as filesystems_tables
from starlingx_dashboard.dashboards.admin.inventory.interfaces import \
    tables as interface_tables
from starlingx_dashboard.dashboards.admin.inventory.kubernetes_labels import \
    tables as label_tables
from starlingx_dashboard.dashboards.admin.inventory.lldp import \
    tables as lldp_tables
from starlingx_dashboard.dashboards.admin.inventory.memories import \
    tables as memory_tables
from starlingx_dashboard.dashboards.admin.inventory.ports import \
    tables as port_tables
from starlingx_dashboard.dashboards.admin.inventory.sensors import \
    tables as sensor_tables
from starlingx_dashboard.dashboards.admin.inventory.storages import \
    tables as storage_tables
from starlingx_dashboard.dashboards.admin.inventory import \
    tables as toplevel_tables

LOG = logging.getLogger(__name__)


class HostsTab(tabs.TableTab):
    table_classes = (toplevel_tables.HostsController,
                     toplevel_tables.HostsStorage,
                     toplevel_tables.HostsWorker,
                     toplevel_tables.HostsUnProvisioned,)
    name = _("Hosts")
    slug = "hosts"
    template_name = ("admin/inventory/_hosts.html")

    # for optimization, the complete hosts list, and phosts list from
    # patching service, are in class scope.
    all_hosts = []
    all_phosts = []

    def get_all_hosts_data(self):
        request = self.request
        self.all_hosts = []
        try:
            self.all_hosts = stx_api.sysinv.host_list(request)
        # In a DC environment with one subcloud controller, when the
        # subcloud is offline and the page is refreshed,
        # TypeError and CommunicationError exception are being caught.
        # The user is redirected to System
        # controller and have visibility of the subcloud status.
        except (TypeError, exc.CommunicationError):
            if(getattr(settings, 'DC_MODE', False)):
                failure_url = "/auth/switch_services_region/" \
                              "SystemController/?next=/dc_admin/"
                msg = (_('Subcloud is unavailable, '
                         'redirected to SystemController region'))
                exceptions.handle(request, msg, redirect=failure_url)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve host list.'))
        self.all_phosts = []
        try:
            self.all_phosts = stx_api.patch.get_hosts(request)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve host list from'
                                ' patching service.'))

    def get_hosts_data(self, personality):
        hosts = self.all_hosts
        phosts = self.all_phosts

        if personality == stx_api.sysinv.PERSONALITY_CONTROLLER:
            hosts = [h for h in hosts if h._personality and
                     h._personality.lower().startswith(
                         stx_api.sysinv.PERSONALITY_CONTROLLER)]
        elif personality == stx_api.sysinv.PERSONALITY_UNKNOWN:
            hosts = [h for h in hosts if not h._personality]
        else:
            hosts = [h for h in hosts if h._personality and
                     h._personality.lower() == personality]

        # Add patching status data to hosts
        for h in hosts:
            for ph in phosts:
                if h.hostname == ph.hostname:
                    if ph.interim_state is True:
                        h.patch_current = "Pending"
                    elif ph.patch_failed is True:
                        h.patch_current = "Failed"
                    else:
                        h.patch_current = ph.patch_current
                    h.requires_reboot = ph.requires_reboot
                    h._patch_state = ph.state
                    h.allow_insvc_patching = ph.allow_insvc_patching

        # Sort hosts by hostname
        hosts.sort(key=lambda f: f.hostname if f.hostname else '')
        return hosts

    def get_hostscontroller_data(self):
        controllers = self.get_hosts_data(
            stx_api.sysinv.PERSONALITY_CONTROLLER)

        return controllers

    def get_hostsstorage_data(self):
        storages = self.get_hosts_data(stx_api.sysinv.PERSONALITY_STORAGE)

        return storages

    def get_hostsworker_data(self):
        workers = self.get_hosts_data(stx_api.sysinv.PERSONALITY_WORKER)

        return workers

    def get_hostsunprovisioned_data(self):
        unprovisioned = self.get_hosts_data(stx_api.sysinv.PERSONALITY_UNKNOWN)

        return unprovisioned

    def load_table_data(self):
        # Calls the get_{{ table_name }}_data methods for each table class
        # and sets the data on the tables
        self.get_all_hosts_data()
        return super(HostsTab, self).load_table_data()

    def get_context_data(self, request):
        # Adds a {{ table_name }}_table item to the context for each table
        # in the table_classes attribute
        context = super(HostsTab, self).get_context_data(request)

        controllers = context['hostscontroller_table'].data
        storages = context['hostsstorage_table'].data
        workers = context['hostsworker_table'].data
        unprovisioned = context['hostsunprovisioned_table'].data

        context['controllers'] = controllers
        context['storages'] = storages
        context['workers'] = workers
        context['unprovisioned'] = unprovisioned

        totals = []
        ctrl_cnt = 0
        comp_cnt = 0
        stor_cnt = 0
        degr_cnt = 0
        fail_cnt = 0

        for h in controllers:
            ctrl_cnt += 1
            if h._availability == 'degraded':
                degr_cnt += 1
            elif h._availability == 'failed':
                fail_cnt += 1

        for h in storages:
            stor_cnt += 1
            if h._availability == 'degraded':
                degr_cnt += 1
            elif h._availability == 'failed':
                fail_cnt += 1

        for h in workers:
            comp_cnt += 1
            if h._availability == 'degraded':
                degr_cnt += 1
            elif h._availability == 'failed':
                fail_cnt += 1

        if (ctrl_cnt > 0):
            badge = "badge-success"
            totals.append(
                {'name': "Controller", 'value': ctrl_cnt, 'badge': badge})

        if (stor_cnt > 0):
            badge = "badge-success"
            totals.append(
                {'name': "Storage", 'value': stor_cnt, 'badge': badge})

        if (comp_cnt > 0):
            badge = "badge-success"
            totals.append(
                {'name': "Worker", 'value': comp_cnt, 'badge': badge})

        if (degr_cnt > 0):
            badge = "badge-warning"
        else:
            badge = ""
        totals.append({'name': "Degraded", 'value': degr_cnt, 'badge': badge})

        if (fail_cnt > 0):
            badge = "badge-danger"
        else:
            badge = ""
        totals.append({'name': "Failed", 'value': fail_cnt, 'badge': badge})

        context['totals'] = totals
        return context


class DeviceUsageTab(tabs.TableTab):
    table_classes = (device_tables.DeviceUsageTable, )
    name = _("Device Usage")
    slug = "deviceusage"
    template_name = ("admin/inventory/_deviceusage.html")
    preload = False

    def get_sysinv_devices(self, request):
        device_list = stx_api.sysinv.device_list_all(request)
        return device_list

    def get_device_description(self, usage, devices):
        # Correlate the (device_id, vendor_id) or class_id to the
        # Sysinv view of devices to get a user-friendly description to
        # display.
        for device in devices:
            if (usage.device_id == device.pdevice_id and
                    usage.vendor_id == device.pvendor_id):
                return device.pdevice
            elif (usage.class_id == device.pclass_id):
                return device.pclass

    def get_deviceusage_data(self):
        deviceusage = []
        devices = []
        try:
            deviceusage = stx_api.nova.get_device_usage_list(self.request)
            devices = self.get_sysinv_devices(self.request)
            for du in deviceusage:
                du.description = self.get_device_description(du, devices)
        except Exception:
            # exceptions.handle(self.request,
            #                   _('Unable to retrieve device usage.'))
            pass

        return deviceusage


class InventoryTabs(tabs.TabGroup):
    slug = "inventory"
    tabs = (
        HostsTab, DeviceUsageTab)
    sticky = True


class OverviewTab(tabs.TableTab):
    table_classes = (
        cpufunctions_tables.CpuFunctionsTable, port_tables.PortsTable,
        interface_tables.InterfacesTable)
    name = _("Overview")
    slug = "overview"
    template_name = ("admin/inventory/_detail_overview.html")

    def get_cpufunctions_data(self):
        host = self.tab_group.kwargs['host']
        return host.core_assignment

    def get_ports_data(self):
        host = self.tab_group.kwargs['host']
        host.ports.sort(key=lambda f: (f.name))
        return host.ports

    def get_interfaces_data(self):
        host = self.tab_group.kwargs['host']

        # add 'ports' member to interface class for easier mgmt in table
        if host.interfaces:
            for i in host.interfaces:
                if i.iftype == 'ethernet':
                    i.ports = [p.uuid for p in host.ports if
                               i.uuid == p.interface_uuid]
                    i.portNameList = [p.get_port_display_name() for p in
                                      host.ports if
                                      i.uuid == p.interface_uuid]
                    i.dpdksupport = [p.dpdksupport for p in host.ports if
                                     i.uuid == p.interface_uuid]
                elif i.iftype == 'vlan':
                    for u in i.uses:
                        for j in host.interfaces:
                            if j.ifname == str(u):
                                if j.iftype == 'ethernet':
                                    i.dpdksupport = [p.dpdksupport for p in
                                                     host.ports if
                                                     j.uuid ==
                                                     p.interface_uuid]
                                elif j.iftype == 'ae':
                                    for ae_u in j.uses:
                                        for k in host.interfaces:
                                            if k.ifname == str(ae_u):
                                                i.dpdksupport = [
                                                    p.dpdksupport for p in
                                                    host.ports if
                                                    k.uuid ==
                                                    p.interface_uuid]
                elif i.iftype == 'ae':
                    for u in i.uses:
                        for j in host.interfaces:
                            if j.ifname == str(u):
                                i.dpdksupport = [p.dpdksupport for p in
                                                 host.ports if
                                                 j.uuid == p.interface_uuid]

        host.interfaces.sort(key=lambda f: (f.ifname))
        return host.interfaces

    def get_context_data(self, request):
        context = super(OverviewTab, self).get_context_data(request)
        try:
            context['host'] = self.tab_group.kwargs['host']
        except Exception:
            redirect = reverse('horizon:admin:inventory:index')
            exceptions.handle(self.request,
                              _('Unable to retrieve inventory details.'),
                              redirect=redirect)
        return context


class CpuFunctionsTab(tabs.TableTab):
    table_classes = (cpufunctions_tables.CpuFunctionsTable, )
    name = _("Processor")
    slug = "cpufunctions"
    template_name = ("admin/inventory/_detail_cpufunctions.html")

    def get_cpufunctions_data(self):
        host = self.tab_group.kwargs['host']
        return host.core_assignment

    def get_context_data(self, request):
        context = super(CpuFunctionsTab, self).get_context_data(request)
        try:
            context['host'] = self.tab_group.kwargs['host']
        except Exception:
            redirect = reverse('horizon:admin:inventory:index')
            exceptions.handle(self.request,
                              _('Unable to retrieve inventory details.'),
                              redirect=redirect)
        return context


class MemorysTab(tabs.TableTab):
    table_classes = (memory_tables.MemorysTable, )
    name = _("Memory")
    slug = "memorys"
    template_name = ("admin/inventory/_detail_memorys.html")

    def get_memorys_data(self):
        host = self.tab_group.kwargs['host']
        host.memorys.sort(key=lambda f: (f.numa_node))
        return host.memorys


class StorageTab(tabs.TableTab):
    table_classes = (storage_tables.DisksTable,
                     storage_tables.StorageVolumesTable,
                     storage_tables.PhysicalVolumesTable,
                     storage_tables.LocalVolumeGroupsTable,
                     storage_tables.PartitionsTable,)
    name = _("Storage")
    slug = "storages"
    template_name = ("admin/inventory/_detail_storages.html")

    def get_disks_data(self):
        host = self.tab_group.kwargs['host']
        return host.disks

    def get_storagevolumes_data(self):
        host = self.tab_group.kwargs['host']
        return host.stors

    def get_physicalvolumes_data(self):
        host = self.tab_group.kwargs['host']
        return host.pvs

    def get_localvolumegroups_data(self):
        host = self.tab_group.kwargs['host']
        return host.lvgs

    def get_partitions_data(self):
        host = self.tab_group.kwargs['host']
        return host.partitions

    def get_context_data(self, request):
        context = super(StorageTab, self).get_context_data(request)
        host = self.tab_group.kwargs['host']
        try:
            context['host'] = host
        except Exception:
            redirect = reverse('horizon:admin:inventory:index')
            exceptions.handle(self.request,
                              _('Unable to retrieve inventory details.'),
                              redirect=redirect)

        context['is_host_with_storage'] =  \
            stx_api.sysinv.is_host_with_storage(request, host.uuid)

        return context


class PortsTab(tabs.TableTab):
    table_classes = (port_tables.PortsTable, )
    name = _("Ports")
    slug = "ports"
    template_name = ("admin/inventory/_detail_ports.html")

    def get_ports_data(self):
        host = self.tab_group.kwargs['host']
        host.ports.sort(key=lambda f: (f.name))
        return host.ports


class InterfacesTab(tabs.TableTab):
    table_classes = (interface_tables.InterfacesTable, )
    name = _("Interfaces")
    slug = "interfaces"
    template_name = ("admin/inventory/_detail_interfaces.html")

    def get_interfaces_data(self):
        host = self.tab_group.kwargs['host']

        # add 'ports' member to interface class for easier mgmt in table
        if host.interfaces:
            for i in host.interfaces:
                i.host_id = host.id

                port_data = \
                    list(map(list, list(zip(*[(p.get_port_display_name(),
                             p.neighbours) for p in host.ports if
                             i.uuid == p.interface_uuid]))))

                if port_data:
                    # Default interface
                    i.portNameList = port_data[0]
                    i.portNeighbourList = port_data[1]
                else:
                    # Non-default interface, no port data
                    i.portNameList = []
                    i.portNeighbourList = []

                platform_network_names = []
                if i.ifclass == 'platform':
                    for interface_network in stx_api.sysinv.\
                            interface_network_list_by_interface(
                            self.request, i.uuid):
                        platform_network_names.append(
                            interface_network.network_name)
                i.platform_network_names = platform_network_names

                data_network_names = []
                if i.ifclass in ['data', 'pci-passthrough', 'pci-sriov']:
                    for interface_datanetwork in stx_api.sysinv.\
                            interface_datanetwork_list_by_interface(
                            self.request, i.uuid):
                        data_network_names.append(
                            interface_datanetwork.datanetwork_name)
                i.data_network_names = data_network_names

                if i.iftype == 'ethernet':
                    i.dpdksupport = [p.dpdksupport for p in host.ports if
                                     i.uuid == p.interface_uuid]
                elif i.iftype == 'vlan':
                    for u in i.uses:
                        for j in host.interfaces:
                            if j.ifname == str(u):
                                if j.iftype == 'ethernet':
                                    i.dpdksupport = [p.dpdksupport for p in
                                                     host.ports if
                                                     j.uuid ==
                                                     p.interface_uuid]
                                elif j.iftype == 'ae':
                                    for ae_u in j.uses:
                                        for k in host.interfaces:
                                            if k.ifname == str(ae_u):
                                                i.dpdksupport = [
                                                    p.dpdksupport for p in
                                                    host.ports if
                                                    k.uuid ==
                                                    p.interface_uuid]
                elif i.iftype == 'ae':
                    for u in i.uses:
                        for j in host.interfaces:
                            if j.ifname == str(u):
                                i.dpdksupport = [p.dpdksupport for p in
                                                 host.ports if
                                                 j.uuid == p.interface_uuid]

        host.interfaces.sort(key=lambda f: (f.ifname))
        return host.interfaces


class SensorTab(tabs.TableTab):
    table_classes = (sensor_tables.SensorsTable,
                     sensor_tables.SensorGroupsTable,)
    name = _("Sensors")
    slug = "sensors"
    template_name = ("admin/inventory/_detail_sensors.html")

    def get_sensorgroups_data(self):
        host = self.tab_group.kwargs['host']

        # To extract the sensors in this group
        if host.sensorgroups:
            for i in host.sensorgroups:
                i.host_id = host.id
                i.sensors = [s.uuid for s in host.sensors if
                             i.uuid == s.sensorgroup_uuid]
                i.sensorNameList = [s.get_sensor_display_name()
                                    for s in host.sensors
                                    if i.uuid == s.sensorgroup_uuid]

        return host.sensorgroups

    def get_sensors_data(self):
        host = self.tab_group.kwargs['host']
        if host.sensors:
            for i in host.sensors:
                i.host_id = host.id
                i.sensorgroups = [s.uuid for s in host.sensorgroups if
                                  i.sensorgroup_uuid == s.uuid]
                i.sensorgroupNameList = [s.get_sensorgroup_display_name()
                                         for s in host.sensorgroups
                                         if i.sensorgroup_uuid == s.uuid]
        return host.sensors
        # .sort(key=lambda s: (s.status))

    def get_context_data(self, request):
        context = super(SensorTab, self).get_context_data(request)

        sensors = self.get_sensors_data()

        context["critical"] = len(
            [s for s in sensors if (s.status == 'critical' and
             s.suppress != 'True')])
        context["major"] = len([s for s in sensors if (s.status == 'major' and
                               s.suppress != 'True')])
        context["minor"] = len([s for s in sensors if (s.status == 'minor' and
                               s.suppress != 'True')])
        context["suppressed"] = \
            len([s for s in sensors if s.suppress == 'True'])
        context["total"] = len(sensors)

        try:
            context['host'] = self.tab_group.kwargs['host']
        except Exception:
            redirect = reverse('horizon:admin:inventory:index')
            exceptions.handle(self.request,
                              _('Unable to retrieve inventory details.'),
                              redirect=redirect)
        return context


class DevicesTab(tabs.TableTab):
    table_classes = (device_tables.DevicesTable, )
    name = _("Devices")
    slug = "devices"
    template_name = ("admin/inventory/_detail_devices.html")

    def get_devices_data(self):
        host = self.tab_group.kwargs['host']
        if host.devices:
            for d in host.devices:
                d.host_id = host.id
        return host.devices


class LldpTab(tabs.TableTab):
    table_classes = (lldp_tables.LldpNeighboursTable,)
    name = _("LLDP")
    slug = "lldp"
    template_name = ("admin/inventory/_detail_lldp.html")

    def get_neighbours_data(self):
        host = self.tab_group.kwargs['host']
        # The LLDP neighbours data have been retrieved when HostDetailTabs
        # is loaded
        host.lldpneighbours.sort(key=lambda f: f.port_name)
        return host.lldpneighbours


class LabelsTab(tabs.TableTab):
    table_classes = (label_tables.LabelTable, )
    name = _("Labels")
    slug = "labels"
    template_name = ("admin/inventory/_detail_labels.html")

    def get_labels_data(self):
        host = self.tab_group.kwargs['host']
        host.labels.sort(key=lambda f: (f.host_uuid))
        return host.labels


class FilesystemsTab(tabs.TableTab):
    table_classes = (filesystems_tables.FilesystemsTable, )
    name = _("Filesystems")
    slug = "filesystems"
    template_name = ("admin/inventory/_detail_filesystems.html")

    def get_filesystems_data(self):
        host = self.tab_group.kwargs['host']
        host.filesystems.sort(key=lambda f: (f.name))
        return host.filesystems


class HostDetailTabs(tabs.TabGroup):
    slug = "inventory_details"
    tabs = (OverviewTab, CpuFunctionsTab, MemorysTab, StorageTab,
            FilesystemsTab, PortsTab, InterfacesTab, LldpTab, SensorTab,
            DevicesTab, LabelsTab,)
    sticky = True

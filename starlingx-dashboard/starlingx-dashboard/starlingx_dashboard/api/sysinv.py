#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
#
# Copyright (c) 2013-2023, 2025 Wind River Systems, Inc.
#

from __future__ import absolute_import

import datetime
import logging
import math

from cgtsclient.v1 import client as cgts_client
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard.api import base

import cgcs_patch.constants as patch_constants
import sysinv.common.constants as constants

SYSTEM_TYPE_STANDARD = constants.TIS_STD_BUILD
SYSTEM_TYPE_AIO = constants.TIS_AIO_BUILD

APPARMOR_STATE_ENABLED = constants.APPARMOR_STATE_ENABLED
APPARMOR_STATE_DISABLED = constants.APPARMOR_STATE_DISABLED

PERSONALITY_CONTROLLER = 'controller'
PERSONALITY_WORKER = 'worker'
PERSONALITY_NETWORK = 'network'
PERSONALITY_STORAGE = 'storage'
PERSONALITY_UNKNOWN = 'unknown'

SUBFUNCTIONS_WORKER = 'worker'
SUBFUNCTIONS_LOWLATENCY = 'lowlatency'

RECORDTYPE_INSTALL = 'install'
RECORDTYPE_INSTALL_ANSWER = 'install_answers'
RECORDTYPE_RECONFIG = 'reconfig'

INSTALL_OUTPUT_TEXT = 'text'
INSTALL_OUTPUT_GRAPHICAL = 'graphical'

# Sensor Actions Choices
SENSORS_AC_NOACTIONSCONFIGURABLE = "NoActionsConfigurable"
SENSORS_AC_NONE = "None"
SENSORS_AC_IGNORE = "ignore"
SENSORS_AC_LOG = "log"
SENSORS_AC_ALARM = "alarm"
SENSORS_AC_RESET = "reset"
SENSORS_AC_POWERCYCLE = "power-cycle"
SENSORS_AC_POWEROFF = "poweroff"

# Storage backend values
STORAGE_BACKEND_LVM = "lvm"
STORAGE_BACKEND_CEPH = "ceph"
STORAGE_BACKEND_ROOK_CEPH_STORE = "ceph-rook-store"
STORAGE_BACKEND_CEPH_STORE = "ceph-store"

# Local Volume Group Values
LVG_NOVA_LOCAL = "nova-local"
LVG_CGTS_VG = "cgts-vg"
LVG_CINDER_VOLUMES = "cinder-volumes"
LVG_DEL = 'removing'
LVG_ADD = 'adding'
LVG_PROV = 'provisioned'

# Physical Volume Values
PV_ADD = 'adding'
PV_DEL = 'removing'

# Storage: Volume Group Parameter Types
LVG_CINDER_PARAM_LVM_TYPE = 'lvm_type'
LVG_CINDER_LVM_TYPE_THIN = 'thin'
LVG_CINDER_LVM_TYPE_THICK = 'thick'

# Storage: User Created Partitions
USER_PARTITION_PHYS_VOL = constants.USER_PARTITION_PHYSICAL_VOLUME
PARTITION_STATUS_MSG = constants.PARTITION_STATUS_MSG
PARTITION_IN_USE_STATUS = constants.PARTITION_IN_USE_STATUS

# The default size of a stor's journal in GB. This should be the
# same value as journal_default_size from sysinv.conf.
JOURNAL_DEFAULT_SIZE = 1

# Platform configuration
PLATFORM_CONFIGURATION = '/etc/platform/platform.conf'

# Kubernetes Labels
K8S_LABEL_OPENSTACK_CONTROL_PLANE = 'openstack-control-plane'
K8S_LABEL_OPENSTACK_COMPUTE_NODE = 'openstack-compute-node'
K8S_LABEL_OPENVSWITCH = 'openvswitch'
K8S_LABEL_SRIOV = 'sriov'

CLOCK_SYNCHRONIZATION_CHOICES = (
    (constants.NTP, _("ntp")),
    (constants.PTP, _("ptp")),
)

# Host Board Management Constants
HOST_BM_TYPE_DEPROVISIONED = "none"
HOST_BM_TYPE_IPMI = "ipmi"
HOST_BM_TYPE_REDFISH = "redfish"
HOST_BM_TYPE_DYNAMIC = "dynamic"

# Load states
ACTIVE_LOAD_STATE = 'active'
INACTIVE_LOAD_STATE = 'inactive'
IMPORTED_LOAD_STATE = 'imported'

LOG = logging.getLogger(__name__)


def cgtsclient(request):
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)

    # FIXME this returns the wrong URL
    endpoint = base.url_for(request, 'platform')
    version = 1

    LOG.debug('cgtsclient connection created using token "%s" and url "%s"',
              request.user.token.id, endpoint)
    LOG.debug('user_id=%(user)s, tenant_id=%(tenant)s',
              {'user': request.user.id, 'tenant': request.user.tenant_id})

    return cgts_client.Client(version=version,
                              endpoint=endpoint,
                              auth_url=base.url_for(request, 'identity'),
                              token=request.user.token.id,  # os_auth_token
                              username=request.user.username,
                              password=request.user.token.id,
                              tenant_id=request.user.tenant_id,  # os_tenant_id
                              insecure=insecure, cacert=cacert)


class Label(base.APIResourceWrapper):
    """Wrapper for Inventory Labels"""

    _attrs = ['uuid',
              'label_key',
              'label_value',
              'host_uuid'
              ]

    def __init__(self, apiresource):
        super(Label, self).__init__(apiresource)


def host_label_list(request, host_id):
    labels = cgtsclient(request).label.list(host_id)
    return [Label(n) for n in labels]


def host_label_get(request, label_id):
    label = cgtsclient(request).label.get(label_id)
    if not label:
        raise ValueError('No match found for label ID "%s".' % label_id)
    return Label(label)


def host_label_assign(request, host_uuid, label):
    return cgtsclient(request).label.assign(host_uuid, label)


def host_label_remove(request, label_id):
    return cgtsclient(request).label.remove(label_id)


class Memory(base.APIResourceWrapper):
    """Wrapper for Inventory System"""

    _attrs = ['numa_node',
              'memtotal_mib',
              'platform_reserved_mib',
              'memavail_mib',
              'hugepages_configured',
              'vm_pending_as_percentage',
              'vm_hugepages_nr_2M_pending',
              'vm_hugepages_avail_2M',
              'vm_hugepages_nr_1G_pending',
              'vm_hugepages_avail_1G',
              'vm_hugepages_nr_1G',
              'vm_hugepages_nr_2M',
              'vm_hugepages_nr_4K',
              'vm_hugepages_possible_2M',
              'vm_hugepages_possible_1G',
              'vm_hugepages_use_1G',
              'vswitch_hugepages_reqd',
              'vswitch_hugepages_size_mib',
              'vswitch_hugepages_nr',
              'uuid', 'ihost_uuid', 'inode_uuid',
              'minimum_platform_reserved_mib']

    def __init__(self, apiresource):
        super(Memory, self).__init__(apiresource)


class System(base.APIResourceWrapper):
    """Wrapper for Inventory System"""

    _attrs = ['uuid', 'name', 'system_type', 'system_mode', 'description',
              'software_version', 'capabilities', 'updated_at', 'created_at',
              'location']

    def __init__(self, apiresource):
        super(System, self).__init__(apiresource)

    def get_short_software_version(self):
        if self.software_version:
            return self.software_version.split(" ")[0]
        return None


class Node(base.APIResourceWrapper):
    """Wrapper for Inventory Node (or Socket)"""

    _attrs = ['uuid', 'numa_node', 'capabilities', 'ihost_uuid']

    def __init__(self, apiresource):
        super(Node, self).__init__(apiresource)


class Cpu(base.APIResourceWrapper):
    """Wrapper for Inventory Cpu Cores"""

    _attrs = ['id', 'uuid', 'cpu', 'numa_node', 'core', 'thread',
              'allocated_function',
              'cpu_model', 'cpu_family',
              'capabilities',
              'ihost_uuid', 'inode_uuid']

    def __init__(self, apiresource):
        super(Cpu, self).__init__(apiresource)


class Port(base.APIResourceWrapper):
    """Wrapper for Inventory Ports"""

    _attrs = ['id', 'uuid', 'name', 'namedisplay', 'pciaddr', 'pclass',
              'pvendor', 'pdevice', 'interface_id',
              'psvendor', 'psdevice', 'numa_node', 'mac', 'mtu', 'speed',
              'link_mode', 'capabilities', 'host_uuid', 'interface_uuid',
              'bootp', 'autoneg', 'type', 'sriov_numvfs', 'sriov_totalvfs',
              'sriov_vfs_pci_address', 'sriov_vf_driver', 'max_tx_rate',
              'driver', 'dpdksupport', 'neighbours']

    def __init__(self, apiresource):
        super(Port, self).__init__(apiresource)
        self.autoneg = 'Yes'  # TODO(wrs) Remove this when autoneg supported
        # in DB

    def get_port_display_name(self):
        if self.name:
            return self.name
        if self.namedisplay:
            return self.namedisplay
        else:
            return '(' + str(self.uuid)[-8:] + ')'


class Disk(base.APIResourceWrapper):
    """Wrapper for Inventory Disks"""

    _attrs = ['uuid',
              'device_node',
              'device_path',
              'device_id',
              'device_wwn',
              'device_num',
              'device_type',
              'size_mib',
              'available_mib',
              'rpm',
              'serial_id',
              'capabilities',
              'ihost_uuid',
              'istor_uuid',
              'ipv_uuid']

    def __init__(self, apiresource):
        super(Disk, self).__init__(apiresource)

    def get_model_num(self):
        if 'model_num' in self.capabilities:
            return self.capabilities['model_num']

    @property
    def size_gib(self):
        return math.floor(float(self.size_mib) /  # pylint: disable=W1619
                          1024 * 1000) / 1000.0

    @property
    def available_gib(self):
        return math.floor(float(self.available_mib) /  # pylint: disable=W1619
                          1024 * 1000) / 1000.0


class StorageVolume(base.APIResourceWrapper):
    """Wrapper for Inventory Volumes"""

    _attrs = ['uuid',
              'osdid',
              'state',
              'function',
              'capabilities',
              'idisk_uuid',
              'ihost_uuid',
              'tier_name',
              'journal_path',
              'journal_size_mib',
              'journal_location']

    def __init__(self, apiresource):
        super(StorageVolume, self).__init__(apiresource)

    @property
    def journal_size_gib(self):
        if self.journal_size_mib:
            return self.journal_size_mib // 1024


class PhysicalVolume(base.APIResourceWrapper):
    """Wrapper for Physical Volumes"""

    _attrs = ['uuid',
              'pv_state',
              'pv_type',
              'disk_or_part_uuid',
              'disk_or_part_device_node',
              'disk_or_part_device_path',
              'lvm_pv_name',
              'lvm_vg_name',
              'lvm_pv_uuid',
              'lvm_pv_size',
              'lvm_pe_total',
              'lvm_pe_alloced',
              'ihost_uuid',
              'created_at',
              'updated_at']

    def __init__(self, apiresource):
        super(PhysicalVolume, self).__init__(apiresource)


def host_pv_list(request, host_id):
    pvs = cgtsclient(request).ipv.list(host_id)
    return [PhysicalVolume(n) for n in pvs]


def host_pv_get(request, ipv_id):
    pv = cgtsclient(request).ipv.get(ipv_id)
    if not pv:
        raise ValueError('No match found for pv_id "%s".' % ipv_id)
    return PhysicalVolume(pv)


def host_pv_create(request, **kwargs):
    pv = cgtsclient(request).ipv.create(**kwargs)
    return PhysicalVolume(pv)


def host_pv_delete(request, ipv_id):
    return cgtsclient(request).ipv.delete(ipv_id)


class Partition(base.APIResourceWrapper):
    """Wrapper for Inventory Partitions."""

    _attrs = ['uuid',
              'start_mib',
              'end_mib',
              'size_mib',
              'device_path',
              'type_guid',
              'type_name',
              'idisk_uuid',
              'ipv_uuid',
              'capabilities',
              'ihost_uuid',
              'status']

    def __init__(self, apiresource):
        super(Partition, self).__init__(apiresource)

    @property
    def size_gib(self):
        return math.floor(float(self.size_mib) /  # pylint: disable=W1619
                          1024 * 1000) / 1000.0


def host_disk_partition_list(request, host_id, disk_id=None):
    partitions = cgtsclient(request).partition.list(host_id, disk_id)
    return [Partition(p) for p in partitions]


def host_disk_partition_get(request, partition_id):
    partition = cgtsclient(request).partition.get(partition_id)
    if not partition:
        raise ValueError('No match found for partition_id '
                         '"%s".' % partition_id)
    return Partition(partition)


def host_disk_partition_create(request, **kwargs):
    partition = cgtsclient(request).partition.create(**kwargs)
    return Partition(partition)


def host_disk_partition_update(request, partition_id, **kwargs):
    mypatch = []
    for key, value in kwargs.items():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))

    partition = cgtsclient(request).partition.update(partition_id, mypatch)
    return Partition(partition)


def host_disk_partition_delete(request, partition_id, **kwargs):
    return cgtsclient(request).partition.delete(partition_id)


class LocalVolumeGroup(base.APIResourceWrapper):
    """Wrapper for Inventory Local Volume Groups"""

    _attrs = ['lvm_vg_name',
              'vg_state',
              'uuid',
              'ihost_uuid',
              'capabilities',
              'lvm_vg_access',
              'lvm_max_lv',
              'lvm_cur_lv',
              'lvm_max_pv',
              'lvm_cur_pv',
              'lvm_vg_size',
              'lvm_vg_avail_size',
              'lvm_vg_total_pe',
              'lvm_vg_free_pe',
              'created_at',
              'updated_at']

    def __init__(self, apiresource):
        super(LocalVolumeGroup, self).__init__(apiresource)

    @property
    def lvm_vg_size_gib(self):
        return math.floor(float(  # pylint: disable=W1619
            self.lvm_vg_size) / (1024 ** 3) * 1000) / 1000.0

    @property
    def lvm_vg_avail_size_gib(self):
        return math.floor(float(  # pylint: disable=W1619
            self.lvm_vg_avail_size) / (1024 ** 3) * 1000) / 1000.0


class LocalVolumeGroupParam(object):
    def __init__(self, lvg_id, key, val):
        self.lvg_id = lvg_id
        self.id = key
        self.key = key
        self.value = val


def host_lvg_list(request, host_id, get_params=False):
    lvgs = cgtsclient(request).ilvg.list(host_id)
    if get_params:
        for lvg in lvgs:
            lvg.params = host_lvg_get_params(request, lvg.uuid, True, lvg)
    return [LocalVolumeGroup(n) for n in lvgs]


def host_lvg_get(request, ilvg_id, get_params=False):
    lvg = cgtsclient(request).ilvg.get(ilvg_id)
    if not lvg:
        raise ValueError('No match found for lvg_id "%s".' % ilvg_id)
    if get_params:
        lvg.params = host_lvg_get_params(request, lvg.id, True, lvg)
    return LocalVolumeGroup(lvg)


def host_lvg_create(request, **kwargs):
    lvg = cgtsclient(request).ilvg.create(**kwargs)
    return LocalVolumeGroup(lvg)


def host_lvg_delete(request, ilvg_id):
    return cgtsclient(request).ilvg.delete(ilvg_id)


def host_lvg_update(request, ilvg_id, patch):
    return cgtsclient(request).ilvg.update(ilvg_id, patch)


def host_lvg_get_params(request, lvg_id, raw=False, lvg=None):
    if lvg is None:
        lvg = cgtsclient(request).ilvg.get(lvg_id)
    params = lvg.capabilities
    if raw:
        return params
    return [LocalVolumeGroupParam(lvg_id, key, value) for
            key, value in params.items()]


class Sensor(base.APIResourceWrapper):
    """Wrapper for Sensors"""

    _attrs = ['uuid',
              'status',
              'state',
              'sensortype',
              'datatype',
              'sensorname',
              'actions_critical',
              'actions_major',
              'actions_minor',
              'host_uuid',
              'sensorgroup_uuid',
              'suppress',
              'created_at',
              'updated_at']

    def __init__(self, apiresource):
        super(Sensor, self).__init__(apiresource)

    def get_sensor_display_name(self):
        if self.sensorname:
            return self.sensorname
        else:
            return '(' + str(self.uuid)[-8:] + ')'


def host_sensor_list(request, host_id):
    sensors = cgtsclient(request).isensor.list(host_id)
    return [Sensor(n) for n in sensors]


def host_sensor_get(request, isensor_id):
    sensor = cgtsclient(request).isensor.get(isensor_id)
    if not sensor:
        raise ValueError('No match found for sensor_id "%s".' % isensor_id)
    return Sensor(sensor)


def host_sensor_create(request, **kwargs):
    sensor = cgtsclient(request).isensor.create(**kwargs)
    return Sensor(sensor)


def host_sensor_update(request, sensor_id, **kwargs):
    LOG.debug("sensor_update(): sensor_id=%s, kwargs=%s", sensor_id, kwargs)
    mypatch = []
    for key, value in kwargs.items():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).isensor.update(sensor_id, mypatch)


def host_sensor_suppress(request, sensor_id):
    kwargs = {'suppress': "True"}
    sensor = host_sensor_update(request, sensor_id, **kwargs)
    return sensor


def host_sensor_unsuppress(request, sensor_id):
    kwargs = {'suppress': "False"}
    sensor = host_sensor_update(request, sensor_id, **kwargs)
    return sensor


def host_sensor_delete(request, isensor_id):
    return cgtsclient(request).isensor.delete(isensor_id)


class SensorGroup(base.APIResourceWrapper):
    """Wrapper for Inventory Sensor Groups"""

    _attrs = ['uuid',
              'sensorgroupname',
              'sensortype',
              'state',
              'datatype',
              'sensors',
              'host_uuid',
              'algorithm',
              'actions_critical_group',
              'actions_major_group',
              'actions_minor_group',
              'actions_critical_choices',
              'actions_major_choices',
              'actions_minor_choices',
              'audit_interval_group',
              'suppress',
              'created_at',
              'updated_at']

    ACTIONS_DISPLAY_CHOICES = (
        (None, _("None")),
        (SENSORS_AC_NONE, _("None.")),
        (SENSORS_AC_IGNORE, _("Ignore")),
        (SENSORS_AC_LOG, _("Log")),
        (SENSORS_AC_ALARM, _("Alarm")),
        (SENSORS_AC_RESET, _("Reset Host")),
        (SENSORS_AC_POWERCYCLE, _("Power Cycle Host")),
        (SENSORS_AC_POWEROFF, _("Power Off Host")),
        (SENSORS_AC_NOACTIONSCONFIGURABLE, _("No Configurable Actions")),
    )

    def __init__(self, apiresource):
        super(SensorGroup, self).__init__(apiresource)

    def get_sensorgroup_display_name(self):
        if self.sensorgroupname:
            return self.sensorgroupname
        else:
            return '(' + str(self.uuid)[-8:] + ')'

    @staticmethod
    def _get_display_value(display_choices, data):
        """Lookup the display value in the provided dictionary."""
        display_value = [display for (value, display) in display_choices
                         if value and value.lower() == (data or '').lower()]

        if display_value:
            return display_value[0]
        return None

    def _get_sensorgroup_actions_critical_list(self):
        actions_critical_choices_list = []
        if self.actions_critical_choices:
            actions_critical_choices_list = \
                self.actions_critical_choices.split(",")

        return actions_critical_choices_list

    @property
    def sensorgroup_actions_critical_choices(self):
        dv = self._get_display_value(
            self.ACTIONS_DISPLAY_CHOICES,
            self.actions_critical_choices)

        actions_critical_choices_tuple = (self.actions_critical_choices, dv)

        return actions_critical_choices_tuple

    @property
    def sensorgroup_actions_critical_choices_tuple_list(self):
        actions_critical_choices_list = \
            self._get_sensorgroup_actions_critical_list()

        actions_critical_choices_tuple_list = []
        if not actions_critical_choices_list:
            ac = SENSORS_AC_NOACTIONSCONFIGURABLE
            dv = self._get_display_value(
                self.ACTIONS_DISPLAY_CHOICES, ac)
            actions_critical_choices_tuple_list.append((ac, dv))
        else:
            actions_critical_choices_tuple_set = set()

            ac = SENSORS_AC_IGNORE
            dv = self._get_display_value(
                self.ACTIONS_DISPLAY_CHOICES, ac)

            actions_critical_choices_tuple_set.add((ac, dv))

            for ac in actions_critical_choices_list:
                dv = self._get_display_value(
                    self.ACTIONS_DISPLAY_CHOICES, ac)

                if not dv:
                    dv = ac

                actions_critical_choices_tuple_set.add((ac, dv))

            actions_critical_choices_tuple_list = \
                list(actions_critical_choices_tuple_set)

        LOG.debug("actions_critical_choices_tuple_list=%s",
                  actions_critical_choices_tuple_list)

        return actions_critical_choices_tuple_list

    def _get_sensorgroup_actions_major_list(self):
        actions_major_choices_list = []
        if self.actions_major_choices:
            actions_major_choices_list = \
                self.actions_major_choices.split(",")

        return actions_major_choices_list

    @property
    def sensorgroup_actions_major_choices(self):
        dv = self._get_display_value(
            self.ACTIONS_DISPLAY_CHOICES,
            self.actions_major_choices)

        actions_major_choices_tuple = (self.actions_major_choices, dv)

        return actions_major_choices_tuple

    @property
    def sensorgroup_actions_major_choices_tuple_list(self):
        actions_major_choices_list = self._get_sensorgroup_actions_major_list()

        actions_major_choices_tuple_list = []
        if not actions_major_choices_list:
            ac = SENSORS_AC_NOACTIONSCONFIGURABLE
            dv = self._get_display_value(
                self.ACTIONS_DISPLAY_CHOICES, ac)
            actions_major_choices_tuple_list.append((ac, dv))
        else:
            actions_major_choices_tuple_set = set()

            ac = SENSORS_AC_IGNORE
            dv = self._get_display_value(
                self.ACTIONS_DISPLAY_CHOICES, ac)

            actions_major_choices_tuple_set.add((ac, dv))

            for ac in actions_major_choices_list:
                dv = self._get_display_value(
                    self.ACTIONS_DISPLAY_CHOICES, ac)

                if not dv:
                    dv = ac

                actions_major_choices_tuple_set.add((ac, dv))

            actions_major_choices_tuple_list = \
                list(actions_major_choices_tuple_set)

        LOG.debug("actions_major_choices_tuple_list=%s",
                  actions_major_choices_tuple_list)

        return actions_major_choices_tuple_list

    def _get_sensorgroup_actions_minor_list(self):
        actions_minor_choices_list = []
        if self.actions_minor_choices:
            actions_minor_choices_list = \
                self.actions_minor_choices.split(",")

        return actions_minor_choices_list

    @property
    def sensorgroup_actions_minor_choices(self):
        dv = self._get_display_value(
            self.ACTIONS_DISPLAY_CHOICES,
            self.actions_minor_choices)

        actions_minor_choices_tuple = (self.actions_minor_choices, dv)

        return actions_minor_choices_tuple

    @property
    def sensorgroup_actions_minor_choices_tuple_list(self):
        actions_minor_choices_list = self._get_sensorgroup_actions_minor_list()

        actions_minor_choices_tuple_list = []
        if not actions_minor_choices_list:
            ac = SENSORS_AC_NOACTIONSCONFIGURABLE
            dv = self._get_display_value(
                self.ACTIONS_DISPLAY_CHOICES, ac)
            actions_minor_choices_tuple_list.append((ac, dv))
        else:
            actions_minor_choices_tuple_set = set()

            ac = SENSORS_AC_IGNORE
            dv = self._get_display_value(
                self.ACTIONS_DISPLAY_CHOICES, ac)

            actions_minor_choices_tuple_set.add((ac, dv))

            for ac in actions_minor_choices_list:
                dv = self._get_display_value(
                    self.ACTIONS_DISPLAY_CHOICES, ac)

                if not dv:
                    dv = ac

                actions_minor_choices_tuple_set.add((ac, dv))

            actions_minor_choices_tuple_list = \
                list(actions_minor_choices_tuple_set)

        LOG.debug("actions_minor_choices_tuple_list=%s",
                  actions_minor_choices_tuple_list)

        return actions_minor_choices_tuple_list


def host_sensorgroup_list(request, host_id):
    sensorgroups = cgtsclient(request).isensorgroup.list(host_id)
    return [SensorGroup(n) for n in sensorgroups]


def host_sensorgroup_get(request, isensorgroup_id):
    sensorgroup = cgtsclient(request).isensorgroup.get(isensorgroup_id)
    if not sensorgroup:
        raise ValueError('No match found for sensorgroup_id "%s".' %
                         isensorgroup_id)
    return SensorGroup(sensorgroup)


def host_sensorgroup_create(request, **kwargs):
    sensorgroup = cgtsclient(request).isensorgroup.create(**kwargs)
    return SensorGroup(sensorgroup)


def host_sensorgroup_update(request, sensorgroup_id, **kwargs):
    LOG.debug("sensorgroup_update(): sensorgroup_id=%s, kwargs=%s",
              sensorgroup_id, kwargs)
    mypatch = []
    for key, value in kwargs.items():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).isensorgroup.update(sensorgroup_id, mypatch)


def host_sensorgroup_delete(request, isensorgroup_id):
    return cgtsclient(request).isensorgroup.delete(isensorgroup_id)


def host_sensorgroup_relearn(request, host_uuid):
    LOG.info("relearn sensor model for host %s", host_uuid)
    return cgtsclient(request).isensorgroup.relearn(host_uuid)


def host_sensorgroup_suppress(request, sensorgroup_id):
    kwargs = {'suppress': "True"}
    sensorgroup = host_sensorgroup_update(request, sensorgroup_id, **kwargs)
    return sensorgroup


def host_sensorgroup_unsuppress(request, sensorgroup_id):
    kwargs = {'suppress': "False"}
    sensorgroup = host_sensorgroup_update(request, sensorgroup_id, **kwargs)
    return sensorgroup


class Host(base.APIResourceWrapper):
    """Wrapper for Inventory Hosts"""

    _attrs = ['id', 'uuid', 'hostname', 'personality',
              'subfunctions', 'subfunction_oper', 'subfunction_avail',
              'apparmor', 'location', 'serialid', 'operational',
              'administrative', 'invprovision', 'peers',
              'availability', 'uptime', 'task', 'capabilities',
              'created_at', 'updated_at', 'mgmt_mac', 'mgmt_ip',
              'bm_ip', 'bm_type', 'bm_username',
              'config_status', 'vim_progress_status', 'patch_current',
              'requires_reboot', 'boot_device', 'rootfs_device',
              'install_output', 'console', 'ttys_dcd', 'patch_state',
              'allow_insvc_patching', 'install_state', 'install_state_info',
              'clock_synchronization', 'max_cpu_mhz_configured',
              'max_cpu_mhz_allowed']

    PERSONALITY_DISPLAY_CHOICES = (
        (PERSONALITY_CONTROLLER, _("Controller")),
        (PERSONALITY_WORKER, _("Worker")),
        (PERSONALITY_NETWORK, _("Network")),
        (PERSONALITY_STORAGE, _("Storage")),
    )
    ADMIN_DISPLAY_CHOICES = (
        ('locked', _("Locked")),
        ('unlocked', _("Unlocked")),
    )
    OPER_DISPLAY_CHOICES = (
        ('disabled', _("Disabled")),
        ('enabled', _("Enabled")),
    )

    APPARMOR_DISPLAY_CHOICES = (
        (APPARMOR_STATE_ENABLED, _("enabled")),
        (APPARMOR_STATE_DISABLED, _("disabled")),
    )

    AVAIL_DISPLAY_CHOICES = (
        ('available', _("Available")),
        ('intest', _("In-Test")),
        ('degraded', _("Degraded")),
        ('failed', _("Failed")),
        ('power-off', _("Powered-Off")),
        ('offline', _("Offline")),
        ('online', _("Online")),
        ('offduty', _("Offduty")),
        ('dependency', _("Dependency")),
    )
    CONFIG_STATUS_DISPLAY_CHOICES = (
        ('up_to_date', _("up-to-date")),
        ('out_of_date', _("out-of-date")),
    )
    PATCH_STATE_DISPLAY_CHOICES = (
        (patch_constants.PATCH_AGENT_STATE_IDLE,
         _("Idle")),
        (patch_constants.PATCH_AGENT_STATE_INSTALLING,
         _("Patch Installing")),
        (patch_constants.PATCH_AGENT_STATE_INSTALL_FAILED,
         _("Patch Install Failed")),
        (patch_constants.PATCH_AGENT_STATE_INSTALL_REJECTED,
         _("Patch Install Rejected")),
    )

    INSTALL_STATE_DISPLAY_CHOICES = (
        (constants.INSTALL_STATE_PRE_INSTALL, _("Pre-install")),
        (constants.INSTALL_STATE_INSTALLING, _("Installing Packages")),
        (constants.INSTALL_STATE_POST_INSTALL, _("Post-install")),
        (constants.INSTALL_STATE_FAILED, _("Install Failed")),
        (constants.INSTALL_STATE_INSTALLED, _("Installed")),
        (constants.INSTALL_STATE_BOOTING, _("Booting")),
        (constants.INSTALL_STATE_COMPLETED, _("Completed")),
    )

    def __init__(self, apiresource):
        super(Host, self).__init__(apiresource)
        self._personality = self.personality
        self._subfunctions = self.subfunctions
        self._subfunction_oper = self.subfunction_oper
        self._subfunction_avail = self.subfunction_avail
        self._apparmor = self.apparmor
        self._location = self.location
        self._peers = self.peers
        self._bm_type = self.bm_type
        self._administrative = self.administrative
        self._invprovision = self.invprovision
        self._operational = self.operational
        self._availability = self.availability
        self._capabilities = self.capabilities
        self._ttys_dcd = self.ttys_dcd
        self.patch_current = "N/A"
        self.requires_reboot = "N/A"
        self.allow_insvc_patching = True
        self._patch_state = patch_constants.PATCH_AGENT_STATE_IDLE
        self._clock_synchronizations = self.clock_synchronization

        self._install_state = self.install_state
        if self._install_state is not None:
            self._install_state = self._install_state.strip("+")

    @property
    def personality(self):
        # Override controller personality to retrieve
        # the current activity state which
        # is reported in the hosts location field
        if (self._personality == PERSONALITY_CONTROLLER):
            if (self._capabilities['Personality'] == 'Controller-Active'):
                return _('Controller-Active')
            else:
                return _('Controller-Standby')
        return self._get_display_value(self.PERSONALITY_DISPLAY_CHOICES,
                                       self._personality)

    @property
    def additional_subfunctions(self):
        return len(self._subfunctions.split(',')) > 1

    @property
    def is_cpe(self):
        subfunctions = self._subfunctions.split(',')
        if PERSONALITY_CONTROLLER in subfunctions and \
                PERSONALITY_WORKER in subfunctions:
            return True
        else:
            return False

    @property
    def subfunctions(self):
        return self._subfunctions.split(',')

    @property
    def subfunction_oper(self):
        return self._get_display_value(self.OPER_DISPLAY_CHOICES,
                                       self._subfunction_oper)

    @property
    def subfunction_avail(self):
        return self._get_display_value(self.AVAIL_DISPLAY_CHOICES,
                                       self._subfunction_avail)

    @property
    def apparmor(self):
        return self._get_display_value(self.APPARMOR_DISPLAY_CHOICES,
                                       self._apparmor)

    @property
    def config_required(self):
        return self.config_status == 'config required'

    @property
    def location(self):
        if hasattr(self._location, 'locn'):
            return self._location.locn
        if 'locn' in self._location:
            return self._location['locn']
        else:
            return ''

    @property
    def peers(self):
        if hasattr(self._peers, 'name'):
            return self._peers.name
        if self._peers and 'name' in self._peers:
            return self._peers['name']
        else:
            return ''

    @property
    def boottime(self):
        return timezone.now() - datetime.timedelta(
            seconds=self.uptime)

    @property
    def administrative(self):
        return self._get_display_value(self.ADMIN_DISPLAY_CHOICES,
                                       self._administrative)

    @property
    def operational(self):
        return self._get_display_value(self.OPER_DISPLAY_CHOICES,
                                       self._operational)

    @property
    def availability(self):
        return self._get_display_value(self.AVAIL_DISPLAY_CHOICES,
                                       self._availability)

    @property
    def bm_type(self):
        bm_type = self._bm_type
        return bm_type

    @property
    def ttys_dcd(self):
        return self._ttys_dcd == 'True'

    @property
    def clock_synchronization(self):
        return self._get_display_value(CLOCK_SYNCHRONIZATION_CHOICES,
                                       self._clock_synchronization)

    @property
    def patch_state(self):
        return self._get_display_value(self.PATCH_STATE_DISPLAY_CHOICES,
                                       self._patch_state)

    @property
    def install_state(self):
        return self._get_display_value(self.INSTALL_STATE_DISPLAY_CHOICES,
                                       self._install_state)

    def _get_display_value(self, display_choices, data):
        """Lookup the display value in the provided dictionary."""
        display_value = [display for (value, display) in display_choices
                         if value.lower() == (data or '').lower()]

        if display_value:
            return display_value[0]
        return None


def system_list(request):
    systems = cgtsclient(request).isystem.list()
    return [System(n) for n in systems]


def system_get(request):
    system = cgtsclient(request).isystem.list()[0]
    if not system:
        raise ValueError('No system found.')
    return System(system)


def system_update(request, system_id, **kwargs):
    LOG.debug("system_update(): system_id=%s, kwargs=%s", system_id, kwargs)
    mypatch = []
    for key, value in kwargs.items():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).isystem.update(system_id, mypatch)


def host_create(request, **kwargs):
    LOG.debug("host_create(): kwargs=%s", kwargs)
    host = cgtsclient(request).ihost.create(**kwargs)
    return Host(host)


def host_update(request, host_id, **kwargs):
    LOG.debug("host_update(): host_id=%s, kwargs=%s", host_id, kwargs)
    mypatch = []
    for key, value in kwargs.items():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).ihost.update(host_id, mypatch)


def host_delete(request, host_id):
    LOG.debug("host_delete(): host_id=%s", host_id)
    return cgtsclient(request).ihost.delete(host_id)


def host_lock(request, host_id):
    kwargs = {'action': 'lock'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_force_lock(request, host_id):
    kwargs = {'action': 'force-lock'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_unlock(request, host_id):
    kwargs = {'action': 'unlock'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_force_unlock(request, host_id):
    kwargs = {'action': 'force-unlock'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_reboot(request, host_id):
    kwargs = {'action': 'reboot'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_reset(request, host_id):
    kwargs = {'action': 'reset'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_reinstall(request, host_id):
    kwargs = {'action': 'reinstall'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_power_on(request, host_id):
    kwargs = {'action': 'power-on'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_power_off(request, host_id):
    kwargs = {'action': 'power-off'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_swact(request, host_id):
    kwargs = {'action': 'swact'}
    host = host_update(request, host_id, **kwargs)
    return host


def host_get(request, host_id):
    host = cgtsclient(request).ihost.get(host_id)
    if not host:
        raise ValueError('No match found for host_id "%s".' % host_id)

    # if host received doesn't have this attribute,
    # add it with a default value
    set_host_defaults(host)

    return Host(host)


def host_list(request):
    hosts = cgtsclient(request).ihost.list()

    # if host received doesn't have this attribute,
    # add it with a default value
    for host_data in hosts:
        set_host_defaults(host_data)

    return [Host(n) for n in hosts]


def set_host_defaults(host):
    default_value = None
    attrs_list = Host._attrs

    host_dict = host._info
    for attr in attrs_list:
        if attr not in host_dict:
            LOG.debug("Attribute not found. Adding default value: %s: %s",
                      attr, default_value)
            host._add_details({attr: default_value})

    return


class DNS(base.APIResourceWrapper):
    """..."""

    _attrs = ['isystem_uuid', 'nameservers', 'uuid', 'link']

    def __init__(self, apiresource):
        super(DNS, self).__init__(apiresource)


def dns_update(request, dns_id, **kwargs):
    LOG.debug("dns_update(): dns_id=%s, kwargs=%s", dns_id, kwargs)
    mypatch = []

    for key, value in kwargs.items():
        if key == 'nameservers' and not value:
            value = 'NC'
        mypatch.append(dict(path='/' + key, value=value, op='replace'))

    return cgtsclient(request).idns.update(dns_id, mypatch)


def dns_delete(request, dns_id):
    LOG.debug("dns_delete(): dns_id=%s", dns_id)
    return cgtsclient(request).idns.delete(dns_id)


def dns_get(request, dns_id):
    dns = cgtsclient(request).idns.get(dns_id)
    if not dns:
        raise ValueError('No match found for dns_id "%s".' % dns_id)
    return DNS(dns)


def dns_list(request):
    dns = cgtsclient(request).idns.list()
    return [DNS(n) for n in dns]


class NTP(base.APIResourceWrapper):
    """..."""

    _attrs = ['isystem_uuid', 'ntpservers', 'uuid', 'link']

    def __init__(self, apiresource):
        super(NTP, self).__init__(apiresource)


def ntp_update(request, ntp_id, **kwargs):
    LOG.debug("ntp_update(): ntp_id=%s, kwargs=%s", ntp_id, kwargs)
    mypatch = []

    for key, value in kwargs.items():
        if key == 'ntpservers' and not value:
            value = 'NC'
        mypatch.append(dict(path='/' + key, value=value, op='replace'))

    return cgtsclient(request).intp.update(ntp_id, mypatch)


def ntp_delete(request, ntp_id):
    LOG.debug("ntp_delete(): ntp_id=%s", ntp_id)
    return cgtsclient(request).intp.delete(ntp_id)


def ntp_get(request, ntp_id):
    ntp = cgtsclient(request).intp.get(ntp_id)
    if not ntp:
        raise ValueError('No match found for ntp_id "%s".' % ntp_id)
    return NTP(ntp)


def ntp_list(request):
    ntp = cgtsclient(request).intp.list()
    return [NTP(n) for n in ntp]


class EXTOAM(base.APIResourceWrapper):
    """..."""

    _attrs = ['isystem_uuid', 'oam_subnet', 'oam_gateway_ip',
              'oam_floating_ip', 'oam_c0_ip', 'oam_c1_ip',
              'oam_start_ip', 'oam_end_ip',
              'uuid', 'link', 'region_config']

    def __init__(self, apiresource):
        super(EXTOAM, self).__init__(apiresource)

        if hasattr(self, 'uuid'):
            self._oam_subnet = self.oam_subnet
            self._oam_gateway_ip = self.oam_gateway_ip
            self._oam_floating_ip = self.oam_floating_ip
            self._oam_c0_ip = self.oam_c0_ip
            self._oam_c1_ip = self.oam_c1_ip

            self._region_config = self.region_config
            self._oam_start_ip = self.oam_start_ip or ""
            self._oam_end_ip = self.oam_end_ip or ""
        else:
            self._oam_subnet = None
            self._oam_gateway_ip = None
            self._oam_floating_ip = None
            self._oam_c0_ip = None
            self._oam_c1_ip = None

            self._region_config = None
            self._oam_start_ip = None
            self._oam_end_ip = None

    @property
    def oam_subnet(self):
        return self._oam_subnet

    @property
    def oam_gateway_ip(self):
        return self._oam_gateway_ip

    @property
    def oam_floating_ip(self):
        return self._oam_floating_ip

    @property
    def oam_c0_ip(self):
        return self._oam_c0_ip

    @property
    def oam_c1_ip(self):
        return self._oam_c1_ip

    @property
    def region_config(self):
        return self._region_config

    @property
    def oam_start_ip(self):
        return self._oam_start_ip or ""

    @property
    def oam_end_ip(self):
        return self._oam_end_ip or ""


def extoam_update(request, extoam_id, **kwargs):
    LOG.debug("extoam_update(): extoam_id=%s, kwargs=%s", extoam_id, kwargs)
    # print 'THIS IS IN SYSINV UPDATE: ', kwargs
    mypatch = []
    # print "\nThis is the dns_id: ", dns_id, "\n"
    # print "\nThese are the values in sysinv dns_update: ", kwargs, "\n"
    for key, value in kwargs.items():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).iextoam.update(extoam_id, mypatch)


def extoam_delete(request, extoam_id):
    LOG.debug("extoam_delete(): extoam_id=%s", extoam_id)
    return cgtsclient(request).iextoam.delete(extoam_id)


def extoam_get(request, extoam_id):
    extoam = cgtsclient(request).iextoam.get(extoam_id)
    # print "THIS IS SYSNINV GET"
    if not extoam:
        raise ValueError('No match found for extoam_id "%s".' % extoam_id)
    return EXTOAM(extoam)


def extoam_list(request):
    extoam = cgtsclient(request).iextoam.list()
    # print "THIS IS SYSINV LIST"
    return [EXTOAM(n) for n in extoam]


class Cluster(base.APIResourceWrapper):
    """..."""
    _attrs = ['uuid', 'cluster_uuid', 'type', 'name', 'deployment_model']

    def __init__(self, apiresource):
        super(Cluster, self).__init__(apiresource)

        if hasattr(self, 'uuid'):
            self._uuid = self.uuid
            self._name = self.name
            self._type = self.type
            self._deployment_model = self.deployment_model
            self._cluster_uuid = self.cluster_uuid
        else:
            self._uuid = None
            self._name = None
            self._type = None
            self._cluster_uuid = None

    @property
    def uuid(self):
        return self._uuid

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def deployment_model(self):
        return self._deployment_model

    @property
    def cluster_uuid(self):
        return self._cluster_uuid


def cluster_get(request, name):
    clusters = cgtsclient(request).cluster.list()
    for c in clusters:
        if name == c.name:
            return Cluster(c)
    return None


def cluster_list(request):
    clusters = cgtsclient(request).cluster.list()

    return [Cluster(n) for n in clusters]


class StorageTier(base.APIResourceWrapper):
    """..."""
    _attrs = ['uuid', 'name', 'type', 'status']

    def __init__(self, apiresource):
        super(StorageTier, self).__init__(apiresource)

        if hasattr(self, 'uuid'):
            self._uuid = self.uuid
            self._name = self.name
            self._type = self.type
            self._status = self.status
        else:
            self._uuid = None
            self._name = None
            self._type = None
            self._status = None

    @property
    def uuid(self):
        return self._uuid

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def status(self):
        return self._status


class StorageCeph(base.APIResourceWrapper):
    """..."""

    _attrs = ['cinder_pool_gib', 'kube_pool_gib', 'glance_pool_gib',
              'ephemeral_pool_gib', 'object_pool_gib', 'object_gateway',
              'uuid', 'tier_name', 'link', 'ceph_total_space_gib']

    def __init__(self, apiresource):
        super(StorageCeph, self).__init__(apiresource)

        if hasattr(self, 'uuid'):
            self._tier_name = self.tier_name
            self._cinder_pool_gib = self.cinder_pool_gib
            self._kube_pool_gib = self.kube_pool_gib
            self._glance_pool_gib = self.glance_pool_gib
            self._ephemeral_pool_gib = self.ephemeral_pool_gib
            self._object_pool_gib = self.object_pool_gib
            self._object_gateway = self.object_gateway
            self._ceph_total_space_gib = self.ceph_total_space_gib
        else:
            self._tier_name = None
            self._cinder_pool_gib = None
            self._kube_pool_gib = None
            self._glance_pool_gib = None
            self._ephemeral_pool_gib = None
            self._object_pool_gib = None
            self._object_gateway = None
            self._ceph_total_space_gib = None

    @property
    def tier_name(self):
        return self._tier_name

    @property
    def cinder_pool_gib(self):
        return self._cinder_pool_gib

    @property
    def kube_pool_gib(self):
        return self._kube_pool_gib

    @property
    def glance_pool_gib(self):
        return self._glance_pool_gib

    @property
    def ephemeral_pool_gib(self):
        return self._ephemeral_pool_gib

    @property
    def object_pool_gib(self):
        return self._object_pool_gib

    @property
    def object_gateway(self):
        return self._object_gateway

    @property
    def ceph_total_space_gib(self):
        return self._ceph_total_space_gib


class StorageBackend(base.APIResourceWrapper):
    """..."""
    _attrs = ['isystem_uuid', 'name', 'backend',
              'state', 'task', 'uuid', 'link']

    def __init__(self, apiresource):
        super(StorageBackend, self).__init__(apiresource)

        if hasattr(self, 'uuid'):
            self._name = self.name
            self._backend = self.backend
            self._state = self.state
            self._task = self.task
        else:
            self._backend = None
            self._state = None
            self._task = None

    @property
    def name(self):
        return self._name

    @property
    def backend(self):
        return self._backend

    @property
    def state(self):
        return self._state

    @property
    def task(self):
        return self._task


class ControllerFS(base.APIResourceWrapper):
    """..."""
    _attrs = ['uuid', 'link', 'name', 'size', 'logical_volume', 'replicated',
              'device_path', 'ceph_mon_gib', 'hostname']

    def __init__(self, apiresource):
        super(ControllerFS, self).__init__(apiresource)

        if hasattr(self, 'ceph_mon_gib'):
            self._size = self.ceph_mon_gib
            self._name = 'ceph-mon'
            self._logical_volume = None
            self._replicated = None
            self._uuid = self.uuid

        else:
            self._uuid = self.uuid
            self._name = self.name
            self._logical_volume = self.logical_volume
            self._size = self.size
            self._replicated = self.replicated

    @property
    def uuid(self):
        return self._uuid

    @property
    def name(self):
        return self._name

    @property
    def logical_volume(self):
        return self._logical_volume

    @property
    def size(self):
        return self._size

    @property
    def replicated(self):
        return self._replicated


class HostFilesystem(base.APIResourceWrapper):
    _attrs = ['uuid', 'id', 'name', 'size', 'logical_volume', 'forihostid',
              'ihost_uuid']

    def __init__(self, apiresource):
        super(HostFilesystem, self).__init__(apiresource)


class CephMon(base.APIResourceWrapper):
    """..."""
    _attrs = ['device_path', 'ceph_mon_gib', 'hostname',
              'ihost_uuid', 'uuid', 'link']

    def __init__(self, apiresource):
        super(CephMon, self).__init__(apiresource)

        if hasattr(self, 'uuid'):
            self._device_path = self.device_path
            self._ceph_mon_gib = self.ceph_mon_gib
            self._hostname = self.hostname
            self._ihost_uuid = self.ihost_uuid
        else:
            self._device_path = None
            self._ceph_mon_gib = None
            self._hostname = None
            self._ihost_uuid = None

    @property
    def device_path(self):
        return self._device_path

    @property
    def ceph_mon_gib(self):
        return self._ceph_mon_gib

    @property
    def hostname(self):
        return self._hostname

    @property
    def ihost_uuid(self):
        return self._ihost_uuid


class STORAGE(base.APIResourceWrapper):
    """..."""
    _attrs = ['isystem_uuid', 'platform_gib',
              'img_conversions_gib', 'database_gib', 'uuid', 'link']

    def __init__(self, controller_fs, ceph_mon):
        if controller_fs:
            super(STORAGE, self).__init__(controller_fs)

        self._platform_gib = None
        self._img_conversions_gib = None
        self._database_gib = None
        self._ceph_mon_gib = None

        if hasattr(self, 'uuid'):
            if controller_fs:
                self._platform_gib = controller_fs.platform_gib
                self._img_conversions_gib = controller_fs.img_conversions_gib
                self._database_gib = controller_fs.database_gib

            if ceph_mon:
                self._device_path = ceph_mon.device_path
                self._ceph_mon_gib = ceph_mon.ceph_mon_gib
                self._hostname = ceph_mon.hostname

    @property
    def platform_gib(self):
        return self._platform_gib

    @property
    def database_gib(self):
        return self._database_gib

    @property
    def img_conversions_gib(self):
        return self._img_conversions_gib

    @property
    def ceph_mon_gib(self):
        return self._ceph_mon_gib


def storfs_update(request, controller_fs_id, **kwargs):
    LOG.info("Updating controller fs storage with kwargs=%s", kwargs)

    my_patch = []

    for key, value in kwargs.items():
        my_patch.append(dict(path='/' + key, value=value,
                             op='replace'))

    return cgtsclient(request).controller_fs.update(controller_fs_id, my_patch)


def storfs_update_many(request, system_uuid, **kwargs):
    LOG.info("Updating controller fs storage with kwargs=%s", kwargs)

    patch_list = []

    for key, value in kwargs.items():
        patch = []
        patch.append({'op': 'replace', 'path': '/name', 'value': key})
        patch.append({'op': 'replace', 'path': '/size', 'value': value})
        patch_list.append(patch)

    return cgtsclient(request).controller_fs.update_many(system_uuid,
                                                         patch_list)


def ceph_mon_update(request, ceph_mon_id, **kwargs):
    LOG.info("Updating ceph-mon storage with kwargs=%s", kwargs)

    my_patch = []

    for key, value in kwargs.items():
        my_patch.append(dict(path='/' + key, value=value,
                             op='replace'))

    return cgtsclient(request).ceph_mon.update(ceph_mon_id, my_patch)


def storpool_update(request, storage_ceph_id, **kwargs):
    LOG.info("Updating storage pool with kwargs=%s", kwargs)

    my_patch = []

    for key, value in kwargs.items():
        my_patch.append(dict(path='/' + key, value=value,
                             op='replace'))

    return cgtsclient(request).storage_ceph.update(storage_ceph_id,
                                                   my_patch)


def controllerfs_get(request, name):
    fs_list = controllerfs_list(request)
    for controller_fs in fs_list:
        if controller_fs.name == name:
            return ControllerFS(controller_fs)

    raise ValueError(
        'No match found for filesystem with name "%s".' % name)


def cephmon_get(request, host_id=None):
    cephmon = cgtsclient(request).ceph_mon.list(host_id)
    if not cephmon:
        return None
    return CephMon(cephmon[0])


def storagepool_get(request, storceph_id=None):
    storceph = cgtsclient(request).storage_ceph.get(storceph_id)
    if not storceph:
        return None
    return StorageCeph(storceph)


def cephmon_list(request):
    ceph_mons = cgtsclient(request).ceph_mon.list()
    if not ceph_mons:
        return None
    return [CephMon(n) for n in ceph_mons]


def storagepool_list(request):
    storage_pools = cgtsclient(request).storage_ceph.list()
    if not storage_pools:
        return None
    return [StorageCeph(n) for n in storage_pools]


def storagefs_list(request):
    # Obtain the storage data from controller_fs and ceph_mon.
    ceph_mon_list = cgtsclient(request).ceph_mon.list()

    # Verify if the results are None and if not, extract the first object.
    # - controller_fs is a one row tables, so the first
    # element of the list is also the only one.
    # - ceph_mon has the ceph_mon_gib field identical for all the entries,
    # so the first element is enough for obtaining the needed data.

    controllerfs_obj = None
    mon_obj = None

    if ceph_mon_list:
        # Get storage-0 configuration
        for mon_obj in ceph_mon_list:
            if mon_obj.hostname == constants.STORAGE_0_HOSTNAME:
                break
        else:
            mon_obj = ceph_mon_list[0]

    return [STORAGE(controllerfs_obj, mon_obj)]


def controllerfs_list(request):
    controllerfs = cgtsclient(request).controller_fs.list()
    ceph_mon_list = cgtsclient(request).ceph_mon.list()
    hosts = cgtsclient(request).ihost.list()

    if ceph_mon_list:
        host = None
        for host in hosts:
            # Get any unlocked controller,
            # both have the same configuration
            if (host.personality == constants.CONTROLLER and
                    host.administrative == constants.ADMIN_UNLOCKED):
                break

        if host and is_host_with_storage(request, host.uuid):
            for mon in ceph_mon_list:
                if mon.hostname == host.hostname:
                    controllerfs.append(mon)
                    break

    return [ControllerFS(n) for n in controllerfs]


def storage_tier_list(request, cluster_id):
    storage_tiers = cgtsclient(request).storage_tier.list(cluster_id)

    return [StorageTier(n) for n in storage_tiers]


def storage_backend_list(request):
    backends = cgtsclient(request).storage_backend.list()

    return [StorageBackend(n) for n in backends]


def storage_usage_list(request):
    ulist = cgtsclient(request).storage_backend.usage()
    return ulist


def get_storage_backend(request):
    storage_list = storage_backend_list(request)
    storage_backends = []

    if storage_list:
        for storage in storage_list:
            if hasattr(storage, 'backend'):
                storage_backends.append(storage.backend)

    return storage_backends


def host_filesystems_list(request, host_id):
    filesystems = cgtsclient(request).host_fs.list(host_id)
    return [HostFilesystem(n) for n in filesystems]


def host_filesystems_update(request, host_id, **kwargs):
    patch_list = []

    for key, value in kwargs.items():
        patch = []
        patch.append({'op': 'replace', 'path': '/name', 'value': key})
        patch.append({'op': 'replace', 'path': '/size', 'value': value})
        patch_list.append(patch)

    LOG.info("host_filesystems_update patch_list=%s", patch_list)
    return cgtsclient(request).host_fs.update_many(host_id, patch_list)


def host_node_list(request, host_id):
    nodes = cgtsclient(request).inode.list(host_id)
    return [Node(n) for n in nodes]


def host_node_get(request, node_id):
    node = cgtsclient(request).inode.get(node_id)
    if not node:
        raise ValueError('No match found for node_id "%s".' % node_id)
    return Node(node)


def host_cpu_list(request, host_id):
    cpus = cgtsclient(request).icpu.list(host_id)
    return [Cpu(n) for n in cpus]


def host_cpus_modify(request, host_uuid, cpu_data):

    capabilities = []

    for function, counts in cpu_data.items():
        # We need to go from [2,0] to [{'0': '2'}, {'1': '0'}]
        sockets = []
        for i in range(len(counts)):
            sockets.append({i: counts[i]})
        capabilities.append({
            'function': function,
            'sockets': sockets
        })
    return cgtsclient(request).ihost.host_cpus_modify(host_uuid, capabilities)


def host_cpu_update(request, cpu_id, **kwargs):
    mypatch = []
    for key, value in kwargs.items():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).icpu.update(cpu_id, mypatch)


def host_memory_list(request, host_id):
    memorys = cgtsclient(request).imemory.list(host_id)
    return [Memory(n) for n in memorys]


def host_memory_get(request, memory_id):
    memory = cgtsclient(request).imemory.get(memory_id)
    if not memory:
        raise ValueError('No match found for memory_id "%s".' % memory_id)
    return Memory(memory)


def host_memory_update(request, memory_id, **kwargs):
    mypatch = []
    for key, value in kwargs.items():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).imemory.update(memory_id, mypatch)


def host_port_list(request, host_id):
    ports = cgtsclient(request).ethernet_port.list(host_id)
    return [Port(n) for n in ports]


def host_port_get(request, port_id):
    port = cgtsclient(request).ethernet_port.get(port_id)
    if not port:
        raise ValueError('No match found for port_id "%s".' % port_id)
    return Port(port)


def host_port_update(request, port_id, **kwargs):
    mypatch = []
    for key, value in kwargs.items():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).ethernet_port.update(port_id, mypatch)


def host_disk_list(request, host_id):
    disks = cgtsclient(request).idisk.list(host_id)
    return [Disk(n) for n in disks]


def host_disk_get(request, disk_id):
    disk = cgtsclient(request).idisk.get(disk_id)
    if not disk:
        raise ValueError('No match found for disk_id "%s".' % disk_id)
    return Disk(disk)


def host_stor_list(request, host_id):
    volumes = cgtsclient(request).istor.list(host_id)
    return [StorageVolume(n) for n in volumes]


def host_stor_get(request, stor_id):
    volume = cgtsclient(request).istor.get(stor_id)
    if not volume:
        raise ValueError('No match found for stor_id "%s".' % stor_id)
    return StorageVolume(volume)


def host_stor_create(request, **kwargs):
    stor = cgtsclient(request).istor.create(**kwargs)
    return StorageVolume(stor)


def host_stor_delete(request, stor_id):
    return cgtsclient(request).istor.delete(stor_id)


def host_stor_update(request, stor_id, **kwargs):
    mypatch = []
    for key, value in kwargs.items():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))

    stor = cgtsclient(request).istor.update(stor_id, mypatch)
    return StorageVolume(stor)


def host_stor_get_by_function(request, host_id, function=None):
    volumes = cgtsclient(request).istor.list(host_id)

    if function:
        volumes = [v for v in volumes if v.function == function]

    return [StorageVolume(n) for n in volumes]


class Interface(base.APIResourceWrapper):
    """Wrapper for Inventory Interfaces"""

    _attrs = ['id', 'uuid', 'ifname', 'ifclass', 'iftype', 'imtu', 'imac',
              'aemode', 'txhashpolicy', 'primary_reselect', 'vlan_id',
              'uses', 'used_by', 'ihost_uuid',
              'ipv4_mode', 'ipv6_mode', 'ipv4_pool', 'ipv6_pool',
              'sriov_numvfs', 'sriov_vf_driver', 'max_tx_rate',
              'max_rx_rate']

    def __init__(self, apiresource):
        super(Interface, self).__init__(apiresource)
        if not self.ifname:
            self.ifname = '(' + str(self.uuid)[-8:] + ')'


def host_interface_list(request, host_id):
    interfaces = cgtsclient(request).iinterface.list(host_id)
    return [Interface(n) for n in interfaces]


def host_interface_get(request, interface_id):
    interface = cgtsclient(request).iinterface.get(interface_id)
    if not interface:
        raise ValueError(
            'No match found for interface_id "%s".' % interface_id)
    return Interface(interface)


def host_interface_create(request, **kwargs):
    interface = cgtsclient(request).iinterface.create(**kwargs)
    return Interface(interface)


def host_interface_update(request, interface_id, **kwargs):
    mypatch = []
    for key, value in kwargs.items():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).iinterface.update(interface_id, mypatch)


def host_interface_delete(request, interface_id):
    return cgtsclient(request).iinterface.delete(interface_id)


class Network(base.APIResourceWrapper):
    """Wrapper for Inventory Networks"""
    _attrs = ['id', 'uuid', 'type', 'name', 'mtu', 'link_capacity',
              'vlan_id', 'dynamic', 'pool_uuid']

    def __init__(self, apiresource):
        super(Network, self).__init__(apiresource)


def network_list(request):
    networks = cgtsclient(request).network.list()
    return [Network(n) for n in networks]


def network_get(request, network_uuid):
    network = cgtsclient(request).network.get(network_uuid)
    if not network:
        raise ValueError(
            'No match found for network_uuid "%s".' % network_uuid)
    return Network(network)


def network_create(request, **kwargs):
    network = cgtsclient(request).network.create(**kwargs)
    return Network(network)


def network_delete(request, network_uuid):
    return cgtsclient(request).network.delete(network_uuid)


class InterfaceNetwork(base.APIResourceWrapper):
    """Wrapper for Inventory Interface Networks"""
    _attrs = ['forihostid', 'id', 'uuid', 'interface_id',
              'interface_uuid', 'ifname', 'network_id',
              'network_uuid', 'network_name', 'network_type']

    def __init__(self, apiresource):
        super(InterfaceNetwork, self).__init__(apiresource)


def interface_network_list_by_host(request, host_uuid):
    interface_networks = cgtsclient(request).interface_network.list_by_host(
        host_uuid)
    return [InterfaceNetwork(n) for n in interface_networks]


def interface_network_list_by_interface(request, interface_uuid):
    interface_networks = cgtsclient(request).interface_network.\
        list_by_interface(interface_uuid)
    return [InterfaceNetwork(n) for n in interface_networks]


def interface_network_get(request, interface_network_uuid):
    interface_network = cgtsclient(request).interface_network.get(
        interface_network_uuid)
    if not interface_network:
        raise ValueError(
            'No match found for interface_network_uuid "%s".'
            % interface_network_uuid)
    return InterfaceNetwork(interface_network)


def interface_network_assign(request, **kwargs):
    interface_network = cgtsclient(request).interface_network.assign(**kwargs)
    return InterfaceNetwork(interface_network)


def interface_network_remove(request, interface_network_uuid):
    return cgtsclient(request).interface_network.remove(interface_network_uuid)


class InterfaceDataNetwork(base.APIResourceWrapper):
    """Wrapper for Inventory Interface Networks"""
    _attrs = ['forihostid', 'id', 'uuid', 'interface_id',
              'interface_uuid', 'ifname', 'datanetwork_id',
              'datanetwork_uuid', 'datanetwork_name', 'network_type']

    def __init__(self, apiresource):
        super(InterfaceDataNetwork, self).__init__(apiresource)


def interface_datanetwork_list_by_host(request, host_uuid):
    interface_datanetworks = cgtsclient(request).interface_datanetwork.\
        list_by_host(host_uuid)
    return [InterfaceDataNetwork(n) for n in interface_datanetworks]


def interface_datanetwork_list_by_interface(request, interface_uuid):
    interface_datanetworks = cgtsclient(request).interface_datanetwork.\
        list_by_interface(interface_uuid)
    return [InterfaceDataNetwork(n) for n in interface_datanetworks]


def interface_datanetwork_get(request, interface_datanetwork_uuid):
    interface_datanetwork = cgtsclient(request).interface_datanetwork.get(
        interface_datanetwork_uuid)
    if not interface_datanetwork:
        raise ValueError(
            'No match found for interface_datanetwork_uuid "%s".'
            % interface_datanetwork_uuid)
    return InterfaceDataNetwork(interface_datanetwork)


def interface_datanetwork_assign(request, **kwargs):
    interface_datanetwork = cgtsclient(request).interface_datanetwork.\
        assign(**kwargs)
    return InterfaceNetwork(interface_datanetwork)


def interface_datanetwork_remove(request, interface_datanetwork_uuid):
    return cgtsclient(request).interface_datanetwork.remove(
        interface_datanetwork_uuid)


class Address(base.APIResourceWrapper):
    """Wrapper for Inventory Addresses"""

    _attrs = ['uuid', 'interface_uuid', 'address', 'prefix', 'enable_dad']

    def __init__(self, apiresource):
        super(Address, self).__init__(apiresource)


def address_list_by_interface(request, interface_id):
    addresses = cgtsclient(request).address.list_by_interface(interface_id)
    return [Address(n) for n in addresses]


def address_get(request, address_uuid):
    address = cgtsclient(request).address.get(address_uuid)
    if not address:
        raise ValueError(
            'No match found for address uuid "%s".' % address_uuid)
    return Address(address)


def address_create(request, **kwargs):
    address = cgtsclient(request).address.create(**kwargs)
    return Address(address)


def address_delete(request, address_uuid):
    return cgtsclient(request).address.delete(address_uuid)


class AddressPool(base.APIResourceWrapper):
    """Wrapper for Inventory Address Pools"""

    _attrs = ['uuid', 'name', 'network', 'prefix', 'order', 'ranges']

    def __init__(self, apiresource):
        super(AddressPool, self).__init__(apiresource)


def address_pool_list(request):
    pools = cgtsclient(request).address_pool.list()
    return [AddressPool(p) for p in pools]


def address_pool_get(request, address_pool_uuid):
    pool = cgtsclient(request).address_pool.get(address_pool_uuid)
    if not pool:
        raise ValueError(
            'No match found for address pool uuid "%s".' % address_pool_uuid)
    return AddressPool(pool)


def address_pool_create(request, **kwargs):
    pool = cgtsclient(request).address_pool.create(**kwargs)
    return AddressPool(pool)


def address_pool_delete(request, address_pool_uuid):
    return cgtsclient(request).address_pool.delete(address_pool_uuid)


def address_pool_update(request, address_pool_uuid, **kwargs):
    mypatch = []
    for key, value in kwargs.items():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).address_pool.update(address_pool_uuid, mypatch)


class Route(base.APIResourceWrapper):
    """Wrapper for Inventory Routers"""

    _attrs = ['uuid', 'interface_uuid', 'network',
              'prefix', 'gateway', 'metric']

    def __init__(self, apiresource):
        super(Route, self).__init__(apiresource)


def route_list_by_interface(request, interface_id):
    routees = cgtsclient(request).route.list_by_interface(interface_id)
    return [Route(n) for n in routees]


def route_get(request, route_uuid):
    route = cgtsclient(request).route.get(route_uuid)
    if not route:
        raise ValueError(
            'No match found for route uuid "%s".' % route_uuid)
    return Route(route)


def route_create(request, **kwargs):
    route = cgtsclient(request).route.create(**kwargs)
    return Route(route)


def route_delete(request, route_uuid):
    return cgtsclient(request).route.delete(route_uuid)


class Device(base.APIResourceWrapper):
    """Wrapper for Inventory Devices"""

    _attrs = ['uuid', 'name', 'pciaddr', 'host_uuid',
              'pclass_id', 'pvendor_id', 'pdevice_id',
              'pclass', 'pvendor', 'pdevice',
              'numa_node', 'enabled', 'extra_info',
              'sriov_totalvfs', 'sriov_numvfs', 'sriov_vfs_pci_address']

    def __init__(self, apiresource):
        super(Device, self).__init__(apiresource)
        if not self.name:
            self.name = '(' + str(self.uuid)[-8:] + ')'


def host_device_list(request, host_id):
    devices = cgtsclient(request).pci_device.list(host_id)
    return [Device(n) for n in devices]


def device_list_all(request):
    devices = cgtsclient(request).pci_device.list_all()
    return [Device(n) for n in devices]


def host_device_get(request, device_uuid):
    device = cgtsclient(request).pci_device.get(device_uuid)
    if device:
        return Device(device)
    raise ValueError('No match found for device "%s".' % device_uuid)


def host_device_update(request, device_uuid, **kwargs):
    mypatch = []
    for key, value in kwargs.items():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).pci_device.update(device_uuid, mypatch)


class LldpNeighbour(base.APIResourceWrapper):
    """Wrapper for Inventory LLDP Neighbour"""

    _attrs = ['port_uuid',
              'port_name',
              'port_namedisplay',
              'uuid',
              'host_uuid',
              'msap',
              'chassis_id',
              'port_identifier',
              'port_description',
              'ttl',
              'system_name',
              'system_description',
              'system_capabilities',
              'management_address',
              'dot1_port_vid',
              'dot1_proto_vids',
              'dot1_vlan_names',
              'dot1_proto_ids',
              'dot1_vid_digest',
              'dot1_management_vid',
              'dot1_lag',
              'dot3_mac_status',
              'dot3_power_mdi',
              'dot3_max_frame']

    def __init__(self, apiresource):
        super(LldpNeighbour, self).__init__(apiresource)

    def get_local_port_display_name(self):
        if self.port_name:
            return self.port_name
        if self.port_namedisplay:
            return self.port_namedisplay
        else:
            return '(' + str(self.port_uuid)[-8:] + ')'


def host_lldpneighbour_list(request, host_uuid):
    neighbours = cgtsclient(request).lldp_neighbour.list(host_uuid)
    return [LldpNeighbour(n) for n in neighbours]


def host_lldpneighbour_get(request, neighbour_uuid):
    neighbour = cgtsclient(request).lldp_neighbour.get(neighbour_uuid)

    if not neighbour:
        raise ValueError('No match found for neighbour id "%s".' %
                         neighbour_uuid)
    return LldpNeighbour(neighbour)


def port_lldpneighbour_list(request, port_uuid):
    neighbours = cgtsclient(request).lldp_neighbour.list_by_port(port_uuid)
    return [LldpNeighbour(n) for n in neighbours]


class ServiceParameter(base.APIResourceWrapper):
    """Wrapper for Service Parameter configuration"""

    _attrs = ['uuid', 'service', 'section', 'name', 'value']

    def __init__(self, apiresource):
        super(ServiceParameter, self).__init__(apiresource)


def service_parameter_list(request):
    parameters = cgtsclient(request).service_parameter.list()
    return [ServiceParameter(n) for n in parameters]


class SDNController(base.APIResourceWrapper):
    """Wrapper for SDN Controller configuration"""

    _attrs = ['uuid', 'ip_address', 'port', 'transport', 'state',
              'created_at', 'updated_at']

    def __init__(self, apiresource):
        super(SDNController, self).__init__(apiresource)


def sdn_controller_list(request):
    controllers = cgtsclient(request).sdn_controller.list()
    return [SDNController(n) for n in controllers]


def sdn_controller_get(request, uuid):
    controller = cgtsclient(request).sdn_controller.get(uuid)

    if not controller:
        raise ValueError('No match found for SDN controller id "%s".' %
                         uuid)
    return SDNController(controller)


def sdn_controller_create(request, **kwargs):
    controller = cgtsclient(request).sdn_controller.create(**kwargs)
    return SDNController(controller)


def sdn_controller_update(request, uuid, **kwargs):
    mypatch = []
    for key, value in kwargs.items():
        mypatch.append(dict(path='/' + key, value=value, op='replace'))
    return cgtsclient(request).sdn_controller.update(uuid, mypatch)


def sdn_controller_delete(request, uuid):
    return cgtsclient(request).sdn_controller.delete(uuid)


def get_sdn_enabled(request):
    # The SDN enabled flag is present in the Capabilities
    # of the system table, however capabilties is not exposed
    # as an attribute through system_list() or system_get()
    # at this level. We will therefore check the platform.conf
    # to see if SDN is configured.
    try:
        with open(PLATFORM_CONFIGURATION, 'r') as fd:
            content = fd.readlines()
        sdn_enabled = None
        for line in content:
            if 'sdn_enabled' in line:
                sdn_enabled = line
                break
        sdn_enabled = sdn_enabled.strip('\n').split('=', 1)
        return (sdn_enabled[1].lower() == 'yes')
    except Exception:
        return False


def get_vswitch_type(request):
    try:
        systems = system_list(request)
        system_capabilities = systems[0].to_dict().get('capabilities')
        vswitch_type = system_capabilities.get('vswitch_type', 'none')
        if vswitch_type != 'none':
            return vswitch_type
        else:
            return None
    except Exception:
        return None


def is_system_mode_simplex(request):
    systems = system_list(request)
    system_mode = systems[0].to_dict().get('system_mode')
    if system_mode == constants.SYSTEM_MODE_SIMPLEX:
        return True
    return False


def get_system_type(request):
    systems = system_list(request)
    system_type = systems[0].to_dict().get('system_type')
    return system_type


def get_ceph_storage_model(request):
    cluster = cluster_get(request, constants.CLUSTER_CEPH_DEFAULT_NAME)
    backends = get_storage_backend(request)
    if STORAGE_BACKEND_CEPH not in backends:
        return None
    return cluster.deployment_model


def get_storage_model(request, backend):
    """Returns the deployment model based on the storage backend type."""
    if backend.name == STORAGE_BACKEND_CEPH_STORE:
        return get_ceph_storage_model(request)
    if backend.name == STORAGE_BACKEND_ROOK_CEPH_STORE:
        sb = cgtsclient(request).storage_backend.get(backend.uuid)
        return sb.capabilities.get('deployment_model')

    return None


def is_host_with_storage(request, host_id):
    """Returns True if the host is expected to have storage."""
    storage_backends = storage_backend_list(request)
    if not storage_backends:
        return False

    storage_backend = storage_backends[0]
    storage_model = get_storage_model(request, storage_backend)

    if storage_model == constants.CEPH_AIO_SX_MODEL:
        # We have a single host, no need to query further
        return True

    host = host_get(request, host_id)

    if storage_model == constants.CEPH_STORAGE_MODEL:
        if host._personality == constants.STORAGE:
            return True
        else:
            return False
    elif storage_model == constants.CEPH_CONTROLLER_MODEL:
        if host._personality == constants.CONTROLLER:
            return True
        else:
            return False
    elif storage_model in [
        constants.CEPH_ROOK_DEPLOYMENT_CONTROLLER,
        constants.CEPH_ROOK_DEPLOYMENT_DEDICATED,
        constants.CEPH_ROOK_DEPLOYMENT_OPEN
    ]:
        return True
    else:
        # Storage model is undefined
        return False


class DataNetwork(base.APIResourceWrapper):
    """..."""

    _attrs = ['id', 'uuid', 'network_type', 'name', 'mtu', 'description',
              'multicast_group', 'port_num', 'ttl', 'mode']

    def __init__(self, apiresource):
        super(DataNetwork, self).__init__(apiresource)


DATANETWORK_TYPE_FLAT = "flat"
DATANETWORK_TYPE_VLAN = "vlan"
DATANETWORK_TYPE_VXLAN = "vxlan"

data_network_type_choices_list = [
    (DATANETWORK_TYPE_FLAT, DATANETWORK_TYPE_FLAT),
    (DATANETWORK_TYPE_VLAN, DATANETWORK_TYPE_VLAN),
    (DATANETWORK_TYPE_VXLAN, DATANETWORK_TYPE_VXLAN),
]


def data_network_type_choices():
    return data_network_type_choices_list


def data_network_create(request, **kwargs):
    LOG.info("data_network_create(): kwargs=%s", kwargs)
    datanet = cgtsclient(request).datanetwork.create(**kwargs)
    return DataNetwork(datanet)


def data_network_list(request):
    datanets = cgtsclient(request).datanetwork.list()
    return [DataNetwork(n) for n in datanets]


def data_network_get(request, datanet_id):
    datanet = cgtsclient(request).datanetwork.get(datanet_id)
    if not datanet:
        raise ValueError('No match found for datanet_id "%s".' % datanet_id)
    return DataNetwork(datanet)


def data_network_modify(request, datanet_id, **kwargs):
    LOG.info("data_network_modify(): datanet_id,=%s, kwargs=%s",
             datanet_id, kwargs)
    patch = []
    for key, value in kwargs.items():
        patch.append(dict(path='/' + key, value=value, op='replace'))

    datanet = cgtsclient(request).datanetwork.update(datanet_id, patch)
    if not datanet:
        raise ValueError('No match found for datanet_id "%s".' % datanet_id)
    return DataNetwork(datanet)


def data_network_delete(request, datanet_id):
    LOG.info("data_network_delete(): datanet_id=%s", datanet_id)
    return cgtsclient(request).datanetwork.delete(datanet_id)


class KubeVersion(base.APIResourceWrapper):
    """Wrapper for Kubernetes versions"""

    _attrs = ['version', 'target', 'state']

    def __init__(self, apiresource):
        super(KubeVersion, self).__init__(apiresource)


def kube_version_list(request):
    kube_versions = cgtsclient(request).kube_version.list()
    return [KubeVersion(n) for n in kube_versions]


class Load(base.APIResourceWrapper):
    """Wrapper for Load"""

    _attrs = ['software_version', 'compatible_version', 'required_patches',
              'state']

    def __init__(self, apiresource):
        super(Load, self).__init__(apiresource)


def load_list(request):
    loads = cgtsclient(request).load.list()
    return [Load(n) for n in loads]


def get_sw_versions_for_prestage(request):
    valid_states = [
        ACTIVE_LOAD_STATE,
        IMPORTED_LOAD_STATE,
        INACTIVE_LOAD_STATE
    ]
    loads = load_list(request)
    return [load.software_version for load in loads
            if load.state in valid_states]

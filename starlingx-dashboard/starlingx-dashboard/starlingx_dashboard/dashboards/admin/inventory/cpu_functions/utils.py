#
# Copyright (c) 2013-2021 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.utils.translation import ugettext_lazy as _


PLATFORM_CPU_TYPE = "Platform"
VSWITCH_CPU_TYPE = "Vswitch"
SHARED_CPU_TYPE = "Shared"
APPLICATION_CPU_TYPE = "Application"
ISOLATED_CPU_TYPE = "Application-isolated"
NONE_CPU_TYPE = "None"

CPU_TYPE_LIST = [PLATFORM_CPU_TYPE, VSWITCH_CPU_TYPE,
                 SHARED_CPU_TYPE, APPLICATION_CPU_TYPE, ISOLATED_CPU_TYPE,
                 NONE_CPU_TYPE]

PLATFORM_CPU_TYPE_FORMAT = _("Platform")
VSWITCH_CPU_TYPE_FORMAT = _("vSwitch")
SHARED_CPU_TYPE_FORMAT = _("Shared")
APPLICATION_CPU_TYPE_FORMAT = _("Application")
ISOLATED_CPU_TYPE_FORMAT = _("Application-isolated")
NONE_CPU_TYPE_FORMAT = _("None")

CPU_TYPE_FORMATS = {PLATFORM_CPU_TYPE: PLATFORM_CPU_TYPE_FORMAT,
                    VSWITCH_CPU_TYPE: VSWITCH_CPU_TYPE_FORMAT,
                    SHARED_CPU_TYPE: SHARED_CPU_TYPE_FORMAT,
                    APPLICATION_CPU_TYPE: APPLICATION_CPU_TYPE_FORMAT,
                    ISOLATED_CPU_TYPE: ISOLATED_CPU_TYPE_FORMAT,
                    NONE_CPU_TYPE: NONE_CPU_TYPE_FORMAT}

CPU_TYPE_MATRIX = {
    PLATFORM_CPU_TYPE: {
        "format": PLATFORM_CPU_TYPE_FORMAT,
        "worker-only": False},
    VSWITCH_CPU_TYPE: {
        "format": VSWITCH_CPU_TYPE_FORMAT,
        "worker-only": True},
    SHARED_CPU_TYPE: {
        "format": SHARED_CPU_TYPE_FORMAT,
        "worker-only": True},
    ISOLATED_CPU_TYPE: {
        "format": ISOLATED_CPU_TYPE_FORMAT,
        "worker-only": True}
}


class CpuFunction(object):
    def __init__(self, function):
        self.allocated_function = function
        self.socket_cores = {}
        self.socket_cores_number = {}


def compress_range(c_list):
    c_list.append(999)
    c_list.sort()
    c_sep = ""
    c_item = ""
    c_str = ""
    pn = 0
    for n in c_list:
        if not c_item:
            c_item = "%s" % n
        else:
            if n > (pn + 1):
                if int(pn) == int(c_item):
                    c_str = "%s%s%s" % (c_str, c_sep, c_item)
                else:
                    c_str = "%s%s%s-%s" % (c_str, c_sep, c_item, pn)
                c_sep = ","
                c_item = "%s" % n
        pn = n
    return c_str


def restructure_host_cpu_data(host):
    host.core_assignment = []
    if host.cpus:
        host.cpu_model = host.cpus[0].cpu_model
        host.sockets = len(host.nodes)
        host.hyperthreading = "No"
        host.physical_cores = {}

        core_assignment = {}
        number_of_cores = {}

        for cpu in host.cpus:
            if cpu.numa_node not in host.physical_cores:
                host.physical_cores[cpu.numa_node] = 0
            if cpu.thread == 0:
                host.physical_cores[cpu.numa_node] += 1
            elif cpu.thread > 0:
                host.hyperthreading = "Yes"

            if cpu.allocated_function is None:
                cpu.allocated_function = NONE_CPU_TYPE

            if cpu.allocated_function not in core_assignment:
                core_assignment[cpu.allocated_function] = {}
                number_of_cores[cpu.allocated_function] = {}
            if cpu.numa_node not in core_assignment[cpu.allocated_function]:
                core_assignment[cpu.allocated_function][cpu.numa_node] = [
                    int(cpu.cpu)]
                number_of_cores[cpu.allocated_function][cpu.numa_node] = 1
            else:
                core_assignment[cpu.allocated_function][cpu.numa_node].append(
                    int(cpu.cpu))
                number_of_cores[cpu.allocated_function][cpu.numa_node] += 1

        for f in CPU_TYPE_LIST:
            cpufunction = CpuFunction(f)
            if f in core_assignment:
                host.core_assignment.append(cpufunction)
                for s, cores in core_assignment[f].items():
                    cpufunction.socket_cores[s] = compress_range(cores)
                    cpufunction.socket_cores_number[s] = number_of_cores[f][s]
            else:
                if (f == PLATFORM_CPU_TYPE or
                    (hasattr(host, 'subfunctions') and
                     'worker' in host.subfunctions)):
                    if f != NONE_CPU_TYPE:
                        host.core_assignment.append(cpufunction)
                        for s in range(0, len(host.nodes)):
                            cpufunction.socket_cores[s] = ""
                            cpufunction.socket_cores_number[s] = 0


def check_core_functions(personality, icpus):
    platform_cores = 0
    vswitch_cores = 0
    shared_vcpu_cores = 0
    vm_cores = 0
    for cpu in icpus:
        allocated_function = cpu.allocated_function
        if allocated_function == PLATFORM_CPU_TYPE:
            platform_cores += 1
        elif allocated_function == VSWITCH_CPU_TYPE:
            vswitch_cores += 1
        elif allocated_function == SHARED_CPU_TYPE:
            shared_vcpu_cores += 1
        elif allocated_function in [APPLICATION_CPU_TYPE, ISOLATED_CPU_TYPE]:
            vm_cores += 1

    # No limiations for shared_vcpu cores
    error_string = ""
    if platform_cores == 0:
        error_string = "There must be at least one" \
                       " core for %s." % PLATFORM_CPU_TYPE_FORMAT
    elif 'worker' in personality and vm_cores == 0:
        error_string = "There must be at least one" \
                       " core for %s." % APPLICATION_CPU_TYPE_FORMAT
    return error_string

#
# Copyright (c) 2013-2021 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

import sysinv.common.constants as sysinv_const

from cgtsclient.common import constants
from cgtsclient import exc

from django.utils.translation import ugettext_lazy as _  # noqa
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon.utils import validators
from horizon import workflows

from starlingx_dashboard import api as stx_api
from starlingx_dashboard.api import sysinv

LOG = logging.getLogger(__name__)

PERSONALITY_CHOICES = (
    (stx_api.sysinv.PERSONALITY_WORKER, _("Worker")),
    (stx_api.sysinv.PERSONALITY_CONTROLLER, _("Controller")),
    (stx_api.sysinv.PERSONALITY_STORAGE, _("Storage")),
)

FIELD_LABEL_PERFORMANCE_PROFILE = _("Performance Profile")
PERFORMANCE_CHOICES = (
    (stx_api.sysinv.SUBFUNCTIONS_WORKER, _("Standard")),
    (stx_api.sysinv.SUBFUNCTIONS_WORKER + ',' +
     stx_api.sysinv.SUBFUNCTIONS_LOWLATENCY, _("Low Latency")),
)

PERSONALITY_CHOICES_WITHOUT_STORAGE = (
    (stx_api.sysinv.PERSONALITY_WORKER, _("Worker")),
    (stx_api.sysinv.PERSONALITY_CONTROLLER, _("Controller")),
)

PERSONALITY_CHOICE_CONTROLLER = (
    (stx_api.sysinv.PERSONALITY_CONTROLLER, _("Controller")),
)

BM_TYPES_CHOICES = (
    (sysinv.HOST_BM_TYPE_DEPROVISIONED, _('No Board Management')),
    (sysinv.HOST_BM_TYPE_DYNAMIC, _("Dynamic (learn)")),
    (sysinv.HOST_BM_TYPE_IPMI, _("IPMI")),
    (sysinv.HOST_BM_TYPE_REDFISH, _("Redfish")),
)

MAX_CPU_MHZ_CONFIGURED_CHOICES = (
    ('max_cpu_mhz_allowed', _("Default")),
    ('custom', _("Custom")),
)


class AddHostInfoAction(workflows.Action):
    FIELD_LABEL_PERSONALITY = _("Personality")
    FIELD_LABEL_HOSTNAME = _("Host Name")
    FIELD_LABEL_MGMT_MAC = _("Management MAC Address")
    FIELD_LABEL_MGMT_IP = _("Management IP Address")

    personality = forms.ChoiceField(label=FIELD_LABEL_PERSONALITY,
                                    help_text=_("Host Personality"),
                                    choices=PERSONALITY_CHOICES,
                                    widget=forms.Select(
                                        attrs={'class': 'switchable',
                                               'data-slug': 'personality'}))

    subfunctions = forms.ChoiceField(
        label=FIELD_LABEL_PERFORMANCE_PROFILE,
        choices=PERFORMANCE_CHOICES,
        widget=forms.Select(
            attrs={'class': 'switched',
                   'data-switch-on': 'personality',
                   'data-personality-' +
                   stx_api.sysinv.PERSONALITY_WORKER: _(
                       "Personality Sub-Type")}))

    hostname = forms.RegexField(label=FIELD_LABEL_HOSTNAME,
                                max_length=255,
                                required=False,
                                regex=r'^[\w\.\-]+$',
                                error_messages={
                                    'invalid':
                                        _('Name may only contain letters,'
                                          ' numbers, underscores, '
                                          'periods and hyphens.')},
                                widget=forms.TextInput(
                                    attrs={'class': 'switched',
                                           'data-switch-on': 'personality',
                                           'data-personality-' +
                                           stx_api.sysinv.PERSONALITY_WORKER:
                                               FIELD_LABEL_HOSTNAME,
                                           }))

    mgmt_mac = forms.MACAddressField(
        label=FIELD_LABEL_MGMT_MAC,
        widget=forms.TextInput(
            attrs={'class': 'switched',
                   'data-switch-on': 'personality',
                   'data-personality-' +
                   stx_api.sysinv.PERSONALITY_WORKER: FIELD_LABEL_MGMT_MAC,
                   'data-personality-' +
                   stx_api.sysinv.PERSONALITY_CONTROLLER: FIELD_LABEL_MGMT_MAC,
                   'data-personality-' +
                   stx_api.sysinv.PERSONALITY_STORAGE: FIELD_LABEL_MGMT_MAC,
                   }))

    class Meta(object):
        name = _("Host Info")
        help_text = _(
            "From here you can add the configuration for a new host.")

    def __init__(self, request, *arg, **kwargs):
        super(AddHostInfoAction, self).__init__(request, *arg, **kwargs)

        # pesonality cannot be storage if ceph is not configured
        storage_backend = stx_api.sysinv.get_storage_backend(request)
        if stx_api.sysinv.STORAGE_BACKEND_CEPH not in storage_backend:
            self.fields['personality'].choices = \
                PERSONALITY_CHOICES_WITHOUT_STORAGE

        # All-in-one system, personality can be controller or worker.
        systems = stx_api.sysinv.system_list(request)
        system_type = systems[0].to_dict().get('system_type')
        if system_type == constants.TS_AIO:
            self.fields['personality'].choices = \
                PERSONALITY_CHOICES_WITHOUT_STORAGE

    def clean(self):
        cleaned_data = super(AddHostInfoAction, self).clean()
        return cleaned_data


class UpdateHostInfoAction(workflows.Action):
    host_id = forms.CharField(widget=forms.widgets.HiddenInput)

    personality = forms.ChoiceField(label=_("Personality"),
                                    choices=PERSONALITY_CHOICES,
                                    widget=forms.Select(
                                        attrs={'class': 'switchable',
                                               'data-slug': 'personality'}))

    subfunctions = forms.ChoiceField(
        label=FIELD_LABEL_PERFORMANCE_PROFILE,
        choices=PERFORMANCE_CHOICES,
        widget=forms.Select(
            attrs={'class': 'switched',
                   'data-switch-on': 'personality',
                   'data-personality-' +
                   stx_api.sysinv.PERSONALITY_WORKER: _(
                       "Performance Profile")}))

    hostname = forms.RegexField(label=_("Host Name"),
                                max_length=255,
                                required=False,
                                regex=r'^[\w\.\-]+$',
                                error_messages={
                                    'invalid':
                                    _('Name may only contain letters,'
                                      ' numbers, underscores, '
                                      'periods and hyphens.')},
                                widget=forms.TextInput(
                                    attrs={'class': 'switched',
                                           'data-switch-on': 'personality',
                                           'data-personality-' +
                                           stx_api.sysinv.PERSONALITY_WORKER:
                                               _("Host Name")}))

    cpu_freq_config = forms.ChoiceField(
        label=_("CPU Frequency Configuration"),
        required=True,
        initial='max_cpu_mhz_allowed',
        choices=MAX_CPU_MHZ_CONFIGURED_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'switchable switched',
                'data-switch-on': 'personality',
                'data-personality-' + stx_api.sysinv.PERSONALITY_WORKER:
                    _("CPU Frequency Configuration"),
                'data-slug': 'cpu_freq_config'}))

    max_cpu_mhz_configured = forms.IntegerField(
        label=_("Max CPU Frequency (MHz)"),
        initial=1,
        min_value=1,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'cpu_freq_config',
                'data-cpu_freq_config-custom':
                    'Max CPU Frequency (MHz)'}),
        help_text='Host CPU Cores maximum frequency.')

    location = forms.CharField(label=_("Location"),
                               initial='location',
                               required=False,
                               help_text=_("Physical location of Host."))

    clock_synchronization = forms.ChoiceField(
        label=_("Clock Synchronization"),
        choices=stx_api.sysinv.CLOCK_SYNCHRONIZATION_CHOICES)

    ttys_dcd = forms.BooleanField(
        label=_("Serial Console Data Carrier Detect"),
        required=False,
        help_text=_("Enable serial line data carrier detection. "
                    "When selected, dropping carrier detect on the serial "
                    "port revoke any active session and a new login "
                    "process is initiated when a new connection is detected."))

    class Meta(object):
        name = _("Host Info")
        help_text = _(
            "From here you can update the configuration of the current host.\n"
            "Note: this will not affect the resources allocated to any"
            " existing"
            " instances using this host until the host is rebooted.")

    def __init__(self, request, *args, **kwargs):
        super(UpdateHostInfoAction, self).__init__(request, *args, **kwargs)

        host_id = self.initial['host_id']
        host = stx_api.sysinv.host_get(request, host_id)

        # pesonality cannot be storage if ceph is not configured
        storage_backend = stx_api.sysinv.get_storage_backend(request)
        if stx_api.sysinv.STORAGE_BACKEND_CEPH not in storage_backend:
            self.fields['personality'].choices = \
                PERSONALITY_CHOICES_WITHOUT_STORAGE

        # All-in-one system, personality can only be controller or worker.
        systems = stx_api.sysinv.system_list(request)
        self.system_mode = systems[0].to_dict().get('system_mode')
        self.system_type = systems[0].to_dict().get('system_type')
        if self.system_type == constants.TS_AIO:
            self.fields['personality'].choices = \
                PERSONALITY_CHOICES_WITHOUT_STORAGE

        # hostname cannot be modified once it is set
        if self.initial['hostname']:
            self.fields['hostname'].widget.attrs['readonly'] = 'readonly'
            self.fields['hostname'].required = False

        # subfunctions cannot be modified once it is set
        if self.initial['subfunctions']:
            self.fields['subfunctions'].widget.attrs['readonly'] = 'readonly'
            self.fields['subfunctions'].required = False

        if (host._capabilities.get(
                'is_max_cpu_configurable') in [None, 'not-configurable'] or
                sysinv_const.CONTROLLER in host.subfunctions):
            self.fields['cpu_freq_config'].widget.attrs['readonly'] = \
                'readonly'
            self.fields['cpu_freq_config'].required = False

        if (self.initial['max_cpu_mhz_configured'] is not None and
                self.initial['max_cpu_mhz_configured'] !=
                host.max_cpu_mhz_allowed):
            self.fields['cpu_freq_config'].initial = 'custom'

    def clean_location(self):
        try:
            host_id = self.cleaned_data['host_id']
            host = stx_api.sysinv.host_get(self.request, host_id)
            location = host._location
            location['locn'] = self.cleaned_data.get('location')
            return location
        except Exception:
            msg = _('Unable to get host data')
            exceptions.check_message(["Connection", "refused"], msg)
            raise

    def clean(self):
        cleaned_data = super(UpdateHostInfoAction, self).clean()

        if cleaned_data['cpu_freq_config'] == 'max_cpu_mhz_allowed':
            cleaned_data['max_cpu_mhz_configured'] = 'max_cpu_mhz_allowed'

        disabled = self.fields['personality'].widget.attrs.get('disabled')
        if disabled == 'disabled':
            if self.system_type == constants.TS_AIO:
                self._personality = 'controller'
            cleaned_data['personality'] = self._personality

        if cleaned_data['personality'] == stx_api.sysinv.PERSONALITY_STORAGE:
            self._subfunctions = stx_api.sysinv.PERSONALITY_STORAGE
            cleaned_data['subfunctions'] = self._subfunctions
        elif cleaned_data['personality'] == \
                stx_api.sysinv.PERSONALITY_CONTROLLER:
            if self.system_type == constants.TS_AIO:
                self._subfunctions = (stx_api.sysinv.PERSONALITY_CONTROLLER +
                                      ',' + stx_api.sysinv.PERSONALITY_WORKER)
            else:
                self._subfunctions = stx_api.sysinv.PERSONALITY_CONTROLLER
            cleaned_data['subfunctions'] = self._subfunctions

        return cleaned_data

    def handle(self, request, data):
        host_id = self.initial['host_id']
        try:
            max_cpu_mhz_configured = data['max_cpu_mhz_configured']
            patch = {'max_cpu_mhz_configured': max_cpu_mhz_configured}
            stx_api.sysinv.host_update(request, host_id, **patch)
        except exc.ClientException as ce:
            LOG.error(ce)
            msg = self.failure_message + " " + str(ce)
            self.failure_message = msg
            exceptions.handle(request, msg)
            return False
        except Exception as e:
            msg = str(e)
            exceptions.handle(request, msg)
            return False


class AddHostInfo(workflows.Step):
    action_class = AddHostInfoAction
    contributes = ("personality",
                   "subfunctions",
                   "hostname",
                   "mgmt_mac")


class UpdateHostInfo(workflows.Step):
    action_class = UpdateHostInfoAction
    contributes = ("host_id",
                   "personality",
                   "subfunctions",
                   "hostname",
                   "location",
                   "ttys_dcd",
                   "clock_synchronization",
                   "max_cpu_mhz_configured")


class UpdateInstallParamsAction(workflows.Action):
    INSTALL_OUTPUT_CHOICES = (
        (stx_api.sysinv.INSTALL_OUTPUT_TEXT, _("text")),
        (stx_api.sysinv.INSTALL_OUTPUT_GRAPHICAL, _("graphical")),
    )

    boot_device = forms.CharField(label=_("Boot Device"),
                                  max_length=255,
                                  help_text=_("Device for boot partition."))

    rootfs_device = forms.CharField(label=_("Rootfs Device"),
                                    max_length=255,
                                    help_text=_("Device for "
                                                "rootfs partition."))

    install_output = forms.ChoiceField(label=_("Installation Output"),
                                       choices=INSTALL_OUTPUT_CHOICES,
                                       widget=forms.Select(
                                           attrs={'class': 'switchable',
                                                  'data-slug': 'install_output'
                                                  }))

    console = forms.CharField(label=_("Console"),
                              required=False,
                              help_text=_("Console configuration "
                                          "(eg. 'ttyS0,115200' or "
                                          "empty for none)."))

    class Meta(object):
        name = _("Installation Parameters")
        help_text = _(
            "From here you can update the installation parameters of"
            " the current host.")

    def __init__(self, request, *args, **kwargs):
        super(UpdateInstallParamsAction, self).__init__(request, *args,
                                                        **kwargs)

        host_id = self.initial['host_id']
        host = stx_api.sysinv.host_get(self.request, host_id)

        self.fields['boot_device'].initial = host.boot_device
        self.fields['rootfs_device'].initial = host.rootfs_device
        self.fields['install_output'].initial = host.install_output
        self.fields['console'].initial = host.console

    def clean(self):
        cleaned_data = super(UpdateInstallParamsAction, self).clean()
        return cleaned_data


class UpdateInstallParams(workflows.Step):
    action_class = UpdateInstallParamsAction
    contributes = ("boot_device",
                   "rootfs_device",
                   "install_output",
                   "console")


class BoardManagementAction(workflows.Action):

    FIELD_LABEL_BM_IP = _("Board Management Controller IP Address")
    FIELD_LABEL_BM_USERNAME = _("Board Management Controller User Name")
    FIELD_LABEL_BM_PASSWORD = _("Board Management Controller Password")
    FIELD_LABEL_BM_CONFIRM_PASSWORD = _("Confirm Password")

    bm_type = forms.ChoiceField(
        label=_("Board Management Controller Type "),
        choices=BM_TYPES_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'bm_type'}))

    bm_ip = forms.IPField(
        label=FIELD_LABEL_BM_IP,
        required=False,
        help_text=_(
            "IP address of the Board Management Controller"
            " (e.g. 172.25.0.0)"),
        version=forms.IPv4 | forms.IPv6,
        mask=False,
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'bm_type',
            'data-bm_type-' + sysinv.HOST_BM_TYPE_DYNAMIC:
                FIELD_LABEL_BM_IP,
            'data-bm_type-' + sysinv.HOST_BM_TYPE_IPMI:
                FIELD_LABEL_BM_IP,
            'data-bm_type-' + sysinv.HOST_BM_TYPE_REDFISH:
                FIELD_LABEL_BM_IP}))

    bm_username = forms.CharField(
        label=FIELD_LABEL_BM_USERNAME,
        required=False,
        widget=forms.TextInput(attrs={
            'autocomplete': 'off',
            'class': 'switched',
            'data-switch-on': 'bm_type',
            'data-bm_type-' + sysinv.HOST_BM_TYPE_DYNAMIC:
                FIELD_LABEL_BM_USERNAME,
            'data-bm_type-' + sysinv.HOST_BM_TYPE_IPMI:
                FIELD_LABEL_BM_USERNAME,
            'data-bm_type-' + sysinv.HOST_BM_TYPE_REDFISH:
                FIELD_LABEL_BM_USERNAME}))

    bm_password = forms.RegexField(
        label=FIELD_LABEL_BM_PASSWORD,
        widget=forms.PasswordInput(
            render_value=False,
            attrs={
                'autocomplete': 'off',
                'class': 'switched',
                'data-switch-on': 'bm_type',
                'data-bm_type-' + sysinv.HOST_BM_TYPE_DYNAMIC:
                    FIELD_LABEL_BM_PASSWORD,
                'data-bm_type-' + sysinv.HOST_BM_TYPE_IPMI:
                    FIELD_LABEL_BM_PASSWORD,
                'data-bm_type-' + sysinv.HOST_BM_TYPE_REDFISH:
                    FIELD_LABEL_BM_PASSWORD}),
        regex=validators.password_validator(),
        required=False,
        error_messages={'invalid': validators.password_validator_msg()})

    bm_confirm_password = forms.CharField(
        label=FIELD_LABEL_BM_CONFIRM_PASSWORD,
        widget=forms.PasswordInput(
            render_value=False,
            attrs={
                'autocomplete': 'off',
                'class': 'switched',
                'data-switch-on': 'bm_type',
                'data-bm_type-' + sysinv.HOST_BM_TYPE_DYNAMIC:
                    FIELD_LABEL_BM_CONFIRM_PASSWORD,
                'data-bm_type-' + sysinv.HOST_BM_TYPE_IPMI:
                    FIELD_LABEL_BM_CONFIRM_PASSWORD,
                'data-bm_type-' + sysinv.HOST_BM_TYPE_REDFISH:
                    FIELD_LABEL_BM_CONFIRM_PASSWORD}),
        required=False)

    def clean(self):
        cleaned_data = super(BoardManagementAction, self).clean()
        if cleaned_data.get('bm_type') != \
                sysinv_const.HOST_BM_TYPE_DEPROVISIONED:
            if 'bm_ip' not in cleaned_data or not cleaned_data['bm_ip']:
                raise forms.ValidationError(
                    _('Board management IP address is required.'))

            if 'bm_username' not in cleaned_data or not \
                    cleaned_data['bm_username']:
                raise forms.ValidationError(
                    _('Board management user name is required.'))

            if 'bm_password' in cleaned_data:
                if cleaned_data['bm_password'] != cleaned_data.get(
                        'bm_confirm_password', None):
                    raise forms.ValidationError(
                        _('Board management passwords do not match.'))
        else:
            cleaned_data.pop('bm_ip')
            cleaned_data.pop('bm_username')

        return cleaned_data

    # We have to protect the entire "data" dict because it contains the
    # password and confirm_password strings.
    @sensitive_variables('data')
    def handle(self, request, data):
        # Throw away the password confirmation, we're done with it.
        data.pop('bm_confirm_password', None)


class AddBoardManagementAction(BoardManagementAction):

    class Meta(object):
        name = _("Board Management")
        help_text = _(
            "From here you can add the"
            " configuration for the board management controller.")


class UpdateBoardManagementAction(BoardManagementAction):

    class Meta(object):
        name = _("Board Management")
        help_text = _(
            "From here you can update the"
            " configuration of the board management controller.")


class AddBoardManagement(workflows.Step):
    action_class = AddBoardManagementAction
    contributes = ("bm_type",
                   "bm_ip",
                   "bm_username",
                   "bm_password",
                   "bm_confirm_password")


class UpdateBoardManagement(workflows.Step):
    action_class = UpdateBoardManagementAction
    contributes = ("bm_type",
                   "bm_ip",
                   "bm_username",
                   "bm_password",
                   "bm_confirm_password")


class AddHost(workflows.Workflow):
    slug = "add"
    name = _("Add Host")
    finalize_button_name = _("Add Host")
    success_message = _('Added host "%s".')
    failure_message = _('Unable to add host "%s".')
    default_steps = (AddHostInfo,
                     AddBoardManagement)

    success_url = 'horizon:admin:inventory:index'
    failure_url = 'horizon:admin:inventory:index'

    hostname = None

    def format_status_message(self, message):
        name = self.hostname
        return message % name

    def handle(self, request, data):
        self.hostname = data['hostname']
        self.mgmt_mac = data['mgmt_mac']

        try:
            host = stx_api.sysinv.host_create(request, **data)
            return True if host else False

        except exc.ClientException as ce:
            # Display REST API error on the GUI
            LOG.error(ce)
            msg = self.failure_message + " " + str(ce)
            self.failure_message = msg
            return False
        except Exception as e:
            msg = self.format_status_message(self.failure_message) + str(e)
            exceptions.handle(request, msg)
            return False


class UpdateHost(workflows.Workflow):
    slug = "update"
    name = _("Edit Host")
    finalize_button_name = _("Save")
    success_message = _('Updated host "%s".')
    failure_message = _('Unable to modify host "%s".')
    default_steps = (UpdateHostInfo,
                     UpdateInstallParams,
                     UpdateBoardManagement)

    success_url = 'horizon:admin:inventory:index'
    failure_url = 'horizon:admin:inventory:index'

    hostname = None

    def format_status_message(self, message):
        name = self.hostname or self.context.get('host_id')
        return message % name

    def handle(self, request, data):
        self.hostname = data['hostname']

        try:
            host = stx_api.sysinv.host_get(request, data['host_id'])

            if not data['bm_password']:
                data.pop('bm_password')

            # if not trying to change personality, skip check
            if host._personality == data['personality']:
                data.pop('personality')

            if data.get('rootfs_device') == host.rootfs_device:
                data.pop('rootfs_device')

            if data.get('install_output') == host.install_output:
                data.pop('install_output')

            if data.get('console') == host.console:
                data.pop('console')

            # subfunctions cannot be modified once host is configured
            if host._subfunctions and 'subfunctions' in data:
                data.pop('subfunctions')

            # if not trying to change clock_synchronization, skip check
            if host.clock_synchronization == data['clock_synchronization']:
                data.pop('clock_synchronization')

            host = stx_api.sysinv.host_update(request, **data)
            return True if host else False

        except exc.ClientException as ce:
            # Display REST API error on the GUI
            LOG.error(ce)
            msg = self.failure_message + " " + str(ce)
            self.failure_message = msg
            return False
        except Exception as e:
            msg = self.format_status_message(self.failure_message) + str(e)
            exceptions.handle(request, msg)
            return False

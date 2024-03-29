#
# Copyright (c) 2018-2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import base64
import logging

from dcmanagerclient import exceptions as exc

from django.urls import reverse  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from starlingx_dashboard import api

LOG = logging.getLogger(__name__)


class ApplyCloudStrategyForm(forms.SelfHandlingForm):
    failure_url = 'horizon:dc_admin:dc_orchestration:index'

    def handle(self, request, data):
        try:
            result = api.dc_manager.strategy_apply(request)
            if result:
                messages.success(request, "Strategy apply in progress")
            else:
                messages.error(request, "Strategy apply failed")
        except Exception as ex:
            LOG.exception(ex)
            redirect = reverse(self.failure_url)
            msg = _('Strategy apply failed.')
            exceptions.handle(request, msg,
                              redirect=redirect)
        return True


class CreateCloudStrategyForm(forms.SelfHandlingForm):
    FIELD_LABEL_RELEASE = _("Release")
    FIELD_LABEL_SYSADMIN_PASSWORD = _("sysadmin password")
    failure_url = 'horizon:dc_admin:dc_orchestration:index'

    SUBCLOUD_APPLY_TYPES = (
        ('parallel', _("Parallel")),
        ('serial', _("Serial")),
    )

    STRATEGY_TYPES = (
        ('patch', _("Patch")),
        ('upgrade', _("Upgrade")),
        ('kubernetes', _("Kubernetes")),
        ('firmware', _("Firmware")),
        ('prestage', _("Prestage")),
    )

    SUBCLOUD_TYPES = (
        ('cloud_name', _("Subcloud")),
        ('subcloud_group', _("Subcloud Group")),
    )

    type = forms.ChoiceField(
        label=_("Strategy Type"),
        required=True,
        choices=STRATEGY_TYPES,
        widget=forms.Select(
            attrs={
                'class': 'switchable',
                'data-slug': 'strategy_types',
            }
        )
    )

    to_version = forms.ChoiceField(
        label=_("To version"),
        required=False,
        help_text=_("Select a version to apply the strategy. \
                    Otherwise, it will be updated to the SystemController \
                    active version."),
        widget=forms.Select(
            attrs={
                'class': 'switchable switched',
                'data-switch-on': 'strategy_types',
                'data-strategy_types-kubernetes': _("To version"),
                'data-slug': 'to_version'
            }
        )
    )

    target = forms.ChoiceField(
        label=_("Apply to"),
        required=False,
        choices=SUBCLOUD_TYPES,
        widget=forms.Select(
            attrs={
                'class': 'switchable',
                'data-slug': 'subcloud_types',
                'initial': 'Subcloud'
            }
        )
    )

    cloud_name = forms.ChoiceField(
        label=_("Subcloud"),
        required=True,
        help_text=_("Select subcloud to apply strategy."),
        widget=forms.Select(
            attrs={
                'class': 'switchable switched',
                'data-switch-on': 'subcloud_types',
                'data-subcloud_types-cloud_name': _("Subcloud"),
                'data-slug': 'subcloud_name'
            }
        )
    )
    subcloud_group = forms.CharField(
        label=_("Subcloud Group"),
        required=False,
        help_text=_("Select subcloud group to apply strategy."),
        widget=forms.TextInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'subcloud_types',
                'data-subcloud_types-subcloud_group': _("Subcloud Group")
            }
        )
    )

    stop_on_failure = forms.BooleanField(
        label=_("Stop on Failure"),
        required=False,
        initial=True,
        help_text=_("Determines whether orchestration failure in a "
                    "subcloud prevents application to subsequent subclouds")
    )

    subcloud_apply_type = forms.ChoiceField(
        label=_("Subcloud Apply Type"),
        required=True,
        choices=SUBCLOUD_APPLY_TYPES,
        widget=forms.Select(
            attrs={
                'class': 'switched',
                'data-switch-on': 'subcloud_name',
                'data-subcloud_name-default': _("Subcloud Apply Type")
            }
        )
    )

    max_parallel_subclouds = forms.IntegerField(
        label=_("Maximum Parallel Subclouds"),
        initial=20,
        min_value=2,
        max_value=500,
        required=True,
        error_messages={'invalid': _('Maximum Parallel Subclouds must be '
                                     'between 2 and 500.')},
        widget=forms.TextInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'subcloud_name',
                'data-subcloud_name-default':
                _("Maximum Parallel Subclouds")
            }
        )
    )

    force = forms.BooleanField(
        label=_("Force"),
        initial=False,
        required=False,
        help_text=_('Offline subcloud is not skipped. '
                    'Applicable only when the strategy is created '
                    'to a single subcloud.'),
        widget=forms.CheckboxInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'strategy_types',
                'data-strategy_types-upgrade': _("Force"),
            }
        )
    )

    force_kubernetes = forms.BooleanField(
        label=_("Force"),
        initial=False,
        required=False,
        help_text=_('Force Kube upgrade to a subcloud '
                    'which is in-sync with System Controller'),
        widget=forms.CheckboxInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'strategy_types',
                'data-strategy_types-kubernetes': _("Force")
            }
        )
    )

    upload_only = forms.BooleanField(
        label=_("Upload Only"),
        initial=False,
        required=False,
        help_text=_('Stops strategy after uploading patches to subclouds'),
        widget=forms.CheckboxInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'strategy_types',
                'data-strategy_types-patch': _("Upload Only")
            }
        )
    )

    release = forms.ChoiceField(
        label=FIELD_LABEL_RELEASE,
        required=False,
        help_text=_("Select a version for the strategy to apply. \
                    Otherwise, the System Controller active version \
                    will be used."),
        widget=forms.Select(
            attrs={
                'class': 'switched',
                'data-switch-on': 'strategy_types',
                'data-strategy_types-prestage': FIELD_LABEL_RELEASE,
                'data-slug': 'release'
            }
        )
    )

    sysadmin_password = forms.CharField(
        label=FIELD_LABEL_SYSADMIN_PASSWORD,
        required=False,
        widget=forms.PasswordInput(
            attrs={
                'autocomplete': 'off',
                'class': 'switched',
                'data-switch-on': 'strategy_types',
                'data-strategy_types-prestage':
                    FIELD_LABEL_SYSADMIN_PASSWORD,
                'data-required-when-shown': 'true'
            }
        )
    )

    def __init__(self, request, *args, **kwargs):
        super(CreateCloudStrategyForm, self).__init__(request, *args,
                                                      **kwargs)
        subcloud_list = [('default', 'All subclouds')]
        subclouds = api.dc_manager.subcloud_list(self.request)
        subcloud_list.extend([(c.name, c.name) for c in subclouds])
        self.fields['cloud_name'].choices = subcloud_list
        if self.initial.get('cloud_name', None):
            self.fields['cloud_name'].widget.attrs['disabled'] = 'disabled'

        kube_versions = []
        version = []
        kube_version_list = api.sysinv.kube_version_list(self.request)
        for k in kube_version_list:
            if k.state == "active":
                version = [(k.version, '--')]
                kube_versions[:0] = version
                version = [(k.version, k.version + " - " + k.state)]
                kube_versions.extend(version)
            else:
                version = [(k.version, k.version)]
                kube_versions.extend(version)
        self.fields['to_version'].choices = kube_versions

        release_list = []
        sw_versions = api.sysinv.get_sw_versions_for_prestage(self.request)
        for version in sw_versions:
            release_list.extend([(version, version)])
        empty_release = [('', '--')]
        release_list[:0] = empty_release
        self.fields['release'].choices = release_list

    def clean(self):
        cleaned_data = super(CreateCloudStrategyForm, self).clean()
        if cleaned_data['type'] == 'prestage':
            if (('sysadmin_password' not in cleaned_data) or
                    (not cleaned_data['sysadmin_password'])):
                raise forms.ValidationError(
                    {'sysadmin_password':
                     forms.ValidationError('sysadmin password is required')})
        else:
            cleaned_data.pop('release', None)
            cleaned_data.pop('sysadmin_password', None)
        return cleaned_data

    def handle(self, request, data):
        try:
            # convert keys to use dashes
            for k in data.copy().keys():
                if 'subcloud_group' in k or 'cloud_name' in k:
                    continue
                elif '_' in k:
                    data[k.replace('_', '-')] = data[k]
                    del data[k]
            if data['target'] == 'subcloud_group':
                del data['cloud_name']
                del data['force']
                del data['max-parallel-subclouds']
                del data['subcloud-apply-type']
            else:
                del data['subcloud_group']
                if data['cloud_name'] == 'default':
                    del data['cloud_name']
                    del data['force']
                else:
                    del data['max-parallel-subclouds']
                    del data['subcloud-apply-type']
                    data['force'] = str(data['force']).lower()
            del data['target']
            data['stop-on-failure'] = str(data['stop-on-failure']).lower()
            if data['type'] == 'kubernetes':
                data['force'] = str(data['force-kubernetes']).lower()
            else:
                del data['to-version']
            del data['force-kubernetes']

            if data['type'] == 'patch':
                data['upload-only'] = str(data['upload-only']).lower()
            else:
                del data['upload-only']

            if data['type'] == 'prestage':
                if data['release'] == '':
                    data.pop('release', None)
                data['sysadmin_password'] = base64.b64encode(
                    data['sysadmin-password'].encode("utf-8")).decode("utf-8")
            data.pop('sysadmin-password', None)

            response = api.dc_manager.strategy_create(request, data)
            if not response:
                messages.error(request, "Strategy creation failed")
        except Exception as ex:
            LOG.exception(ex)
            redirect = reverse(self.failure_url)
            msg = _('Strategy creation failed.')
            exceptions.handle(request, msg,
                              redirect=redirect)
        return True


class CreateSubcloudConfigForm(forms.SelfHandlingForm):
    failure_url = 'horizon:dc_admin:dc_orchestration:index'

    APPLY_TYPES = (
        ('parallel', _("Parallel")),
        ('serial', _("Serial")),
    )

    INSTANCE_ACTIONS = (
        ('migrate', _("Migrate")),
        ('stop-start', _("Stop-Start")),
    )

    ALARM_RESTRICTION_TYPES = (
        ('relaxed', _("Relaxed")),
        ('strict', _("Strict")),
    )

    subcloud = forms.ChoiceField(
        label=_("Subcloud"),
        required=True,
        widget=forms.Select())

    storage_apply_type = forms.ChoiceField(
        label=_("Storage Apply Type"),
        required=True,
        choices=APPLY_TYPES,
        widget=forms.Select())

    worker_apply_type = forms.ChoiceField(
        label=_("Worker Apply Type"),
        required=True,
        choices=APPLY_TYPES,
        widget=forms.Select(
            attrs={
                'class': 'switchable',
                'data-slug': 'worker_apply_type'}))

    max_parallel_workers = forms.IntegerField(
        label=_("Maximum Parallel Worker Hosts"),
        initial=2,
        min_value=2,
        max_value=100,
        required=True,
        error_messages={'invalid': _('Maximum Parallel Worker Hosts must be '
                                     'between 2 and 100.')},
        widget=forms.TextInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'worker_apply_type',
                'data-worker_apply_type-parallel':
                    'Maximum Parallel Worker Hosts'}))

    default_instance_action = forms.ChoiceField(
        label=_("Default Instance Action"),
        required=True,
        choices=INSTANCE_ACTIONS,
        widget=forms.Select())

    alarm_restriction_type = forms.ChoiceField(
        label=_("Alarm Restrictions"),
        required=True,
        choices=ALARM_RESTRICTION_TYPES,
        widget=forms.Select())

    def __init__(self, request, *args, **kwargs):
        super(CreateSubcloudConfigForm, self).__init__(request, *args,
                                                       **kwargs)
        subcloud_list = [(api.dc_manager.DEFAULT_CONFIG_NAME,
                          api.dc_manager.DEFAULT_CONFIG_NAME), ]
        subclouds = api.dc_manager.subcloud_list(self.request)
        subcloud_list.extend([(c.name, c.name) for c in subclouds])
        self.fields['subcloud'].choices = subcloud_list

        if self.initial.get('subcloud', None):
            self.fields['subcloud'].widget.attrs['disabled'] = 'disabled'

    def handle(self, request, data):
        try:
            for k in data.copy().keys():
                if '_' in k:
                    data[k.replace('_', '-')] = data[k]
                    del data[k]

            subcloud = data['subcloud']
            if subcloud == api.dc_manager.DEFAULT_CONFIG_NAME:
                subcloud = None
            del data['subcloud']

            response = api.dc_manager.config_update(request, subcloud, data)
            if not response:
                messages.error(request, "Subcloud Strategy Configuration "
                                        "creation failed")

        except exc.APIException as e:
            LOG.error(e.error_message)
            messages.error(request, e.error_message)

            redirect = reverse(self.failure_url)
            exceptions.handle(request, e.error_message, redirect=redirect)
        except Exception:
            redirect = reverse(self.failure_url)
            exceptions.handle(request,
                              "Subcloud Strategy Configuration "
                              "creation failed",
                              redirect=redirect)
        return True


class CreateSubcloudGroupForm(forms.SelfHandlingForm):
    failure_url = 'horizon:dc_admin:dc_orchestration:index'

    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=True)
    description = forms.CharField(max_length=255,
                                  label=_("Description"),
                                  required=False)
    SUBCLOUD_APPLY_TYPES = (
        ('parallel', _("Parallel")),
        ('serial', _("Serial")),
    )

    update_apply_type = forms.ChoiceField(
        label=_("Update Apply Type"),
        required=True,
        choices=SUBCLOUD_APPLY_TYPES,
        widget=forms.Select())

    max_parallel_subclouds = forms.IntegerField(
        label=_("Maximum Parallel Subclouds"),
        initial=2,
        min_value=2,
        max_value=500,
        required=True,
        error_messages={'invalid': _('Maximum Parallel Subclouds must be '
                                     'between 2 and 500.')},
        widget=forms.TextInput())

    def handle(self, request, data):
        try:
            if not data['description']:
                data['description'] = "No description provided"

            response = api.dc_manager.subcloud_group_create(request, **data)
            if not response:
                messages.error(request, "Subcloud Group "
                                        "creation failed")
            else:
                msg = (_('Subcloud Group %s was successfully created.') %
                       data['name'])
                LOG.debug(msg)
                messages.success(request, msg)
        except exc.APIException as e:
            LOG.error(e.error_message)
            messages.error(request, e.error_message)

            redirect = reverse(self.failure_url)
            exceptions.handle(request, e.error_message, redirect=redirect)
        except Exception:
            redirect = reverse(self.failure_url)
            exceptions.handle(request,
                              "Subcloud Group creation failed",
                              redirect=redirect)
        return True


class UpdateSubcloudGroupForm(forms.SelfHandlingForm):
    failure_url = 'horizon:dc_admin:dc_orchestration:index'
    group_id = forms.CharField(label=_("ID"),
                               required=False,
                               widget=forms.TextInput(
                               attrs={'readonly': 'readonly'}))
    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=True)
    description = forms.CharField(max_length=255,
                                  label=_("Description"),
                                  required=False)
    SUBCLOUD_APPLY_TYPES = (
        ('parallel', _("Parallel")),
        ('serial', _("Serial")),
    )

    update_apply_type = forms.ChoiceField(
        label=_("Update Apply Type"),
        required=True,
        choices=SUBCLOUD_APPLY_TYPES,
        widget=forms.Select())

    max_parallel_subclouds = forms.IntegerField(
        label=_("Maximum Parallel Subclouds"),
        min_value=2,
        max_value=500,
        required=True,
        error_messages={'invalid': _('Maximum Parallel Subclouds must be '
                                     'between 2 and 500.')},
        widget=forms.TextInput())

    def handle(self, request, data):
        try:
            group_name = data['name']
            if group_name == api.dc_manager.DEFAULT_GROUP_NAME:
                del data['name']

            response = api.dc_manager.subcloud_group_update(
                request, data['group_id'], **data)
            if not response:
                messages.error(request, "Subcloud Group "
                                        "update failed")
            else:
                msg = (_('Subcloud Group %s was successfully updated.') %
                       group_name)
                LOG.debug(msg)
                messages.success(request, msg)
            return response
        except exc.APIException as e:
            LOG.error(e.error_message)
            messages.error(request, e.error_message)

            redirect = reverse(self.failure_url)
            exceptions.handle(request, e.error_message, redirect=redirect)
        except Exception:
            redirect = reverse(self.failure_url)
            exceptions.handle(request,
                              "Subcloud Group update failed",
                              redirect=redirect)
        return True

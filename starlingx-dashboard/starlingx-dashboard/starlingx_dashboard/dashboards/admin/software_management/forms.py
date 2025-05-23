#
# Copyright (c) 2016-2025 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django.forms import FileField
from django.forms import FileInput
from django.urls import reverse  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from starlingx_dashboard import api as stx_api

LOG = logging.getLogger(__name__)


class MultipleFileInput(FileInput):
    allow_multiple_selected = True


class MultipleFileField(FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class UploadReleaseForm(forms.SelfHandlingForm):
    failure_url = 'horizon:admin:software_management:index'
    release_files = MultipleFileField(
        label=_("Release File(s)"),
        widget=MultipleFileInput(attrs={
            'data-source-file': _('Release File(s)'),
            'multiple': "multiple"}), required=True)

    def __init__(self, *args, **kwargs):
        super(UploadReleaseForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = super(UploadReleaseForm, self).clean()
        return data

    def handle(self, request, data):
        success_responses = []
        failure_responses = []
        iso_sig_pairs = {}

        files = request.FILES.getlist('release_files')

        for f in files:
            if f.name.endswith('.iso'):
                iso_sig_pairs.setdefault(f.name[:-4], {})['iso'] = f
            elif f.name.endswith('.sig'):
                iso_sig_pairs.setdefault(f.name[:-4], {})['sig'] = f
            else:
                try:
                    success_responses.append(
                        stx_api.usm.release_upload_req(request, f, f.name))
                except Exception as ex:
                    failure_responses.append(str(ex))

        # iso and sig file should be uploaded together
        if iso_sig_pairs:
            for base_name, pair in iso_sig_pairs.items():
                if 'iso' in pair and 'sig' in pair:
                    try:
                        success_responses.append(
                            stx_api.usm.release_upload_req(
                                request,
                                release=pair['iso'], name=f'{base_name}.iso',
                                release_extra=pair['sig'],
                                name_extra=f'{base_name}.sig')
                        )
                    except Exception as ex:
                        failure_responses.append(str(ex))
                else:
                    missing_file = 'iso' if 'iso' not in pair else 'sig'
                    failure_responses.append(
                        f"Missing {missing_file} file for {base_name}")

        # Consolidate server responses into one success/error message
        # respectively
        if success_responses:
            if len(success_responses) == 1:
                messages.success(request, success_responses[0])
            else:
                success_msg = ""
                for i in range(len(success_responses)):
                    success_msg += str(i + 1) + ") " + success_responses[i]
                messages.success(request, success_msg)

        if failure_responses:
            if len(failure_responses) == 1:
                messages.error(request, failure_responses[0])
            else:
                error_msg = ""
                for i in range(len(failure_responses)):
                    error_msg += str(i + 1) + ") " + failure_responses[i]
                messages.error(request, error_msg)

        return True


class CreateSoftwareDeployStrategyForm(forms.SelfHandlingForm):
    failure_url = 'horizon:admin:software_management:index'

    STRATEGY_TYPES = (
        ('sw-deploy', _("Software Deploy")),
        ('rollback', _("Rollback")),
    )

    CONTROLLER_APPLY_TYPES = (
        ('serial', _("Serial")),
        ('ignore', _("Ignore")),
    )

    GENERIC_APPLY_TYPES = (
        ('serial', _("Serial")),
        ('parallel', _("Parallel")),
        ('ignore', _("Ignore")),
    )

    INSTANCE_ACTION_TYPES = (
        ('migrate', _("Migrate")),
        ('stop-start', _("Stop-Start")),
    )

    SIMPLEX_INSTANCE_ACTIONS_TYPES = (
        ('stop-start', _("Stop-Start")),
    )

    ALARM_RESTRICTION_TYPES = (
        ('strict', _("Strict")),
        ('relaxed', _("Relaxed")),
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

    release = forms.ChoiceField(
        label=_("Release"),
        required=True,
        widget=forms.Select(
            attrs={
                'class': 'switched',
                'data-switch-on': 'strategy_types',
                'data-strategy_types-sw-deploy': _("Release"),
            }
        ))

    controller_apply_type = forms.ChoiceField(
        label=_("Controller Apply Type"),
        required=True,
        choices=CONTROLLER_APPLY_TYPES,
        widget=forms.Select())

    storage_apply_type = forms.ChoiceField(
        label=_("Storage Apply Type"),
        required=True,
        choices=GENERIC_APPLY_TYPES,
        widget=forms.Select())

    worker_apply_type = forms.ChoiceField(
        label=_("Worker Apply Type"),
        required=True,
        choices=GENERIC_APPLY_TYPES,
        widget=forms.Select(
            attrs={
                'class': 'switchable',
                'data-slug': 'worker_apply_type'}))

    max_parallel_worker_hosts = forms.IntegerField(
        label=_("Maximum Parallel Worker Hosts"),
        initial=2,
        min_value=2,
        max_value=10,
        required=True,
        error_messages={'invalid': _('Maximum Parallel Worker Hosts must be '
                                     'between 2 and 10.')},
        widget=forms.TextInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'worker_apply_type',
                'data-worker_apply_type-parallel':
                    'Maximum Parallel Worker Hosts'}))

    default_instance_action = forms.ChoiceField(
        label=_("Default Instance Action"),
        required=True,
        choices=INSTANCE_ACTION_TYPES,
        widget=forms.Select())

    alarm_restrictions = forms.ChoiceField(
        label=_("Alarm Restrictions"),
        required=True,
        choices=ALARM_RESTRICTION_TYPES,
        widget=forms.Select())

    delete = forms.BooleanField(
        label=_("Delete"),
        initial=False,
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'strategy_types',
                'data-strategy_types-sw-deploy': _("Delete")}))

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)

        releases = stx_api.usm.get_releases(request)
        self.fields['release'].choices = \
            [(release.release_id, release.release_id) for release in releases]

        storage_backend = stx_api.sysinv.get_storage_backend(request)
        if stx_api.sysinv.STORAGE_BACKEND_CEPH not in storage_backend:
            del self.fields['storage_apply_type']

        system_type = stx_api.sysinv.get_system_type(request)
        if system_type == stx_api.sysinv.SYSTEM_TYPE_AIO:
            del self.fields['controller_apply_type']

        if stx_api.sysinv.is_system_mode_simplex(request):
            self.fields['default_instance_action'].choices = \
                self.SIMPLEX_INSTANCE_ACTIONS_TYPES

    def clean(self):
        data = super().clean()
        return data

    def handle(self, request, data):
        if data['type'] == 'rollback':
            rollback = True
            release = None
            delete = None
        else:
            rollback = False
            release = data.get('release')
            delete = data.get('delete')
        try:
            response = stx_api.vim.create_strategy(
                request, stx_api.vim.STRATEGY_SW_DEPLOY,
                data.get('controller_apply_type', 'ignore'),
                data.get('storage_apply_type', 'ignore'), 'ignore',
                data['worker_apply_type'],
                data['max_parallel_worker_hosts'],
                data['default_instance_action'],
                data['alarm_restrictions'],
                release=release, rollback=rollback, delete=delete)
            if not response:
                messages.error(request, "Strategy creation failed")
        except Exception:
            redirect = reverse(self.failure_url)
            exceptions.handle(request, "Strategy creation failed",
                              redirect=redirect)
        return True


class ApplySoftwareDeployStrategyForm(forms.SelfHandlingForm):
    failure_url = 'horizon:admin:software_management:index'
    strategy_name = stx_api.vim.STRATEGY_SW_DEPLOY

    def handle(self, request, data):
        try:
            result = stx_api.vim.apply_strategy(request, self.strategy_name)
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

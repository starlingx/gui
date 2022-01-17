#
# Copyright (c) 2018-2022 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import logging

from django import shortcuts
from django.template.defaultfilters import safe
from django.urls import reverse  # noqa
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import messages
from horizon import tables

from starlingx_dashboard import api

LOG = logging.getLogger(__name__)


# Orchestration Strategy
def get_cached_cloud_strategy(request, table):
    if 'cloudpatchstrategy' not in table.kwargs:
        table.kwargs['cloudpatchstrategy'] = \
            api.dc_manager.get_strategy(request)
    return table.kwargs['cloudpatchstrategy']


class CreateCloudStrategy(tables.LinkAction):
    name = "createcloudstrategy"
    url = "horizon:dc_admin:dc_orchestration:createcloudstrategy"
    verbose_name = _("Create Strategy")
    classes = ("ajax-modal", "btn-create")
    icon = "plus"

    def allowed(self, request, datum):
        try:
            strategy = get_cached_cloud_strategy(request, self.table)

            classes = [c for c in self.classes if c != "disabled"]
            self.classes = classes
            if strategy:
                if "disabled" not in self.classes:
                    self.classes = [c for c in self.classes] + ['disabled']
        except Exception as ex:
            LOG.exception(ex)
        return True


class DeleteCloudStrategy(tables.Action):
    name = "delete_patch_strategy"
    force = False
    disabled = False
    requires_input = False
    icon = 'trash'
    action_type = 'danger'
    verbose_name = _("Delete Strategy")

    def allowed(self, request, datum):
        try:
            strategy = get_cached_cloud_strategy(request, self.table)
            self.disabled = True
            if strategy and strategy.state in ['initial', 'complete', 'failed',
                                               'aborted']:
                self.disabled = False
        except Exception as ex:
            LOG.exception(ex)
        return True

    def get_default_classes(self):
        try:
            if self.disabled:
                return ['disabled']
            return super(DeleteCloudStrategy, self).get_default_classes()
        except Exception as ex:
            LOG.exception(ex)

    def single(self, table, request, obj_id):
        try:
            result = api.dc_manager.strategy_delete(request)
            if result:
                messages.success(request, "Strategy Deleted")
            else:
                messages.error(request, "Strategy delete failed")
        except Exception as ex:
            LOG.exception(ex)
            messages.error(request, str(ex))

        url = reverse('horizon:dc_admin:dc_orchestration:index')
        return shortcuts.redirect(url)


class ApplyCloudStrategy(tables.LinkAction):
    name = "apply_cloud_patch_strategy"
    url = "horizon:dc_admin:dc_orchestration:applycloudstrategy"
    verbose_name = _("Apply Strategy")
    classes = ("ajax-modal", "btn-confirm")
    disabled = False
    requires_input = False

    def allowed(self, request, datum):
        try:
            strategy = get_cached_cloud_strategy(request, self.table)
            self.disabled = False
            if not strategy or strategy.state != 'initial':
                self.disabled = True
        except Exception as ex:
            LOG.exception(ex)
        return True

    def get_default_classes(self):
        try:
            if self.disabled:
                return ['disabled']
            return super(ApplyCloudStrategy, self).get_default_classes()
        except Exception as ex:
            LOG.exception(ex)


class AbortCloudStrategy(tables.Action):
    name = "abort_cloud_patch_strategy"
    requires_input = False
    disabled = False
    action_type = 'danger'
    verbose_name = _("Abort Strategy")
    confirm_message = "You have selected Abort Strategy. " \
                      "Please confirm your selection"

    def allowed(self, request, datum):
        try:
            strategy = get_cached_cloud_strategy(request, self.table)
            self.disabled = False
            if not strategy or strategy.state != 'applying':
                self.disabled = True
        except Exception as ex:
            LOG.exception(ex)
        return True

    def get_default_classes(self):
        try:
            if self.disabled:
                return ['disabled']
            return super(AbortCloudStrategy, self).get_default_classes()
        except Exception as ex:
            LOG.exception(ex)

    def single(self, table, request, obj_id):
        try:
            result = api.dc_manager.strategy_abort(request)
            if result:
                messages.success(request, "Strategy abort in progress")
            else:
                messages.error(request, "Strategy abort failed")
        except Exception as ex:
            LOG.exception(ex)
            messages.error(request, str(ex))

        url = reverse('horizon:dc_admin:dc_orchestration:index')
        return shortcuts.redirect(url)


STEP_STATE_CHOICES = (
    (None, True),
    ("", True),
    ("none", True),
    ("complete", True),
    ("initial", True),
    ("failed", False),
    ("timed-out", False),
    ("aborted", False),
)


def get_apply_percent(cell):
    if '(' in cell and '%)' in cell:
        percent = cell.split('(')[1].split('%)')[0]
        return {'percent': "%d%%" % float(percent)}
    return {}


def get_state(step):
    state = step.state
    if '%' in step.details:
        percent = [s for s in step.details.split(' ') if '%' in s]
        if percent and len(percent):
            percent = percent[0]
            state += " (%s)" % percent
    return state


class UpdateStepRow(tables.Row):
    ajax = True

    def get_data(self, request, cloud_name):
        step = api.dc_manager.step_detail(request, cloud_name)
        return step


class StepFilterAction(tables.FilterAction):
    def filter(self, table, steps, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower().strip()

        def comp(step):
            if (q in step.state.lower() or
               q in step.stage):
                return True
            return False

        return list(filter(comp, steps))


class CloudPatchStepsTable(tables.DataTable):
    cloud = tables.Column('cloud', verbose_name=_('Cloud'))
    stage = tables.Column('stage', verbose_name=_('Stage'))
    state = tables.Column(get_state,
                          verbose_name=_('State'),
                          status=True,
                          status_choices=STEP_STATE_CHOICES,
                          filters=(safe,),
                          cell_attributes_getter=get_apply_percent)
    details = tables.Column('details',
                            verbose_name=_("Details"),)
    started_at = tables.Column('started_at',
                               verbose_name=_('Started At'))
    finished_at = tables.Column('finished_at',
                                verbose_name=_('Finished At'))

    def get_object_id(self, obj):
        return "%s" % obj.cloud

    class Meta(object):
        name = "cloudpatchsteps"
        multi_select = False
        status_columns = ['state', ]
        row_class = UpdateStepRow

        table_actions = (StepFilterAction,
                         CreateCloudStrategy, ApplyCloudStrategy,
                         AbortCloudStrategy, DeleteCloudStrategy)
        verbose_name = _("Steps")
        hidden_title = False


# Cloud Patch Config
class CreateCloudPatchConfig(tables.LinkAction):
    name = "createcloudpatchconfig"
    url = "horizon:dc_admin:dc_orchestration:createcloudpatchconfig"
    verbose_name = _("Create New Cloud Patching Configuration")
    classes = ("ajax-modal", "btn-create")
    icon = "plus"


class EditCloudPatchConfig(tables.LinkAction):
    name = "editcloudpatchconfig"
    url = "horizon:dc_admin:dc_orchestration:editcloudpatchconfig"
    verbose_name = _("Edit Configuration")
    classes = ("ajax-modal",)


class DeleteCloudPatchConfig(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Delete Cloud Patching Configuration",
            "Delete Cloud Patching Configurations",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Deleted Cloud Patching Configuration",
            "Deleted Cloud Patching Configurations",
            count
        )

    def allowed(self, request, config=None):
        if config and config.cloud == api.dc_manager.DEFAULT_CONFIG_NAME:
            return False
        return True

    def delete(self, request, config):
        try:
            api.dc_manager.config_delete(request, config)
        except Exception:
            msg = _('Failed to delete configuration for subcloud %(cloud)') % \
                {'cloud': config, }
            redirect = reverse('horizon:dc_admin:dc_orchestration:index')
            exceptions.handle(request, msg, redirect=redirect)

        url = reverse('horizon:dc_admin:dc_orchestration:index')
        return shortcuts.redirect(url)


class CloudPatchConfigTable(tables.DataTable):
    cloud = tables.Column('cloud', verbose_name=_('Cloud'))
    storage_apply_type = tables.Column('storage_apply_type',
                                       verbose_name=_('Storage Apply Type'))
    worker_apply_type = tables.Column('worker_apply_type',
                                      verbose_name=_('Worker Apply Type'))
    max_parallel_workers = tables.Column(
        'max_parallel_workers', verbose_name=_('Max Parallel Workers'))
    default_instance_action = tables.Column(
        'default_instance_action', verbose_name=_('Default Instance Action'))
    alarm_restriction_type = tables.Column(
        'alarm_restriction_type', verbose_name=_('Alarm Restrictions'))

    def get_object_id(self, obj):
        return "%s" % obj.cloud

    def get_object_display(self, obj):
        return obj.cloud

    class Meta(object):
        name = "cloudpatchconfig"
        multi_select = False
        table_actions = (CreateCloudPatchConfig,)
        row_actions = (EditCloudPatchConfig, DeleteCloudPatchConfig,)
        verbose_name = _("Cloud Patching Configurations")
        hidden_title = False


# Subcloud Group Management
class EditSubcloudGroup(tables.LinkAction):
    name = "editsubcloudgroup"
    url = "horizon:dc_admin:dc_orchestration:editsubcloudgroup"
    verbose_name = _("Edit Subcloud Group")
    classes = ("ajax-modal",)


class DeleteSubcloudGroup(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Delete SubCloud Group",
            "Delete SubCloud Groups",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Deleted SubCloud Group",
            "Deleted SubCloud Groups",
            count
        )

    def allowed(self, request, group=None):
        if group and group.name == api.dc_manager.DEFAULT_GROUP_NAME:
            return False
        return True

    def delete(self, request, group):
        try:
            api.dc_manager.subcloud_group_delete(request, group)
        except Exception:
            msg = _('Failed to delete group %(name)') % \
                {'name': group, }
            redirect = reverse('horizon:dc_admin:dc_orchestration:index')
            exceptions.handle(request, msg, redirect=redirect)

        url = reverse('horizon:dc_admin:dc_orchestration:index')
        return shortcuts.redirect(url)


class CreateSubcloudGroup(tables.LinkAction):
    name = "createsubcloudgroup"
    url = "horizon:dc_admin:dc_orchestration:createsubcloudgroup"
    verbose_name = _("Add Subcloud Group")
    classes = ("ajax-modal", "btn-create")
    icon = "plus"


class SubcloudGroupManagementTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    description = tables.Column('description', verbose_name=_('Description'))
    update_apply_type = tables.Column(
        'update_apply_type', verbose_name=_('Update Apply Type'))
    max_parallel_subclouds = tables.Column(
        'max_parallel_subclouds', verbose_name=_('Max parallel subclouds'))
    created_at = tables.Column(
        'created_at', verbose_name=_('Created at'))
    updated_at = tables.Column(
        'updated_at', verbose_name=_('Updated at'))

    def get_object_id(self, obj):
        return "%s" % obj.name

    def get_object_display(self, obj):
        return obj.name

    class Meta(object):
        name = "subcloudgroupmgmt"
        multi_select = False
        table_actions = (CreateSubcloudGroup,)
        row_actions = (EditSubcloudGroup, DeleteSubcloudGroup,)
        verbose_name = _("Subcloud Group Management")
        hidden_title = False

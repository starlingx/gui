#
# Copyright (c) 2013-2024 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import datetime
import logging

from django import shortcuts
from django.template.defaultfilters import title  # noqa
from django.urls import reverse  # noqa
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import messages
from horizon import tables
from starlingx_dashboard import api as stx_api

LOG = logging.getLogger(__name__)


class UploadRelease(tables.LinkAction):
    name = "releaseupload"
    verbose_name = _("Upload Releases")
    url = "horizon:admin:software_management:releaseupload"
    classes = ("ajax-modal", "btn-create")
    icon = "plus"


class DeleteRelease(tables.BatchAction):
    name = "delete"
    icon = 'trash'
    action_type = 'danger'

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Delete Release",
            "Delete Releases",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Deleted Release",
            "Deleted Releases",
            count
        )

    def allowed(self, request, release=None):

        valid_states = {
            "available",
            "unavailable"
            "committed"
        }
        if release is None:
            return True
        return release.state in valid_states

    def handle(self, table, request, obj_ids):
        try:
            result = stx_api.usm.release_delete_req(request, obj_ids)
            messages.success(request, result)
        except Exception as ex:
            messages.error(request, str(ex))

        url = reverse(table.index_url)
        return shortcuts.redirect(url)


class CommitRelease(tables.BatchAction):
    name = "commit"

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Commit Release",
            "Commit Releases",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Committed Release",
            "Committed Releases",
            count
        )

    def allowed(self, request, release=None):
        if release is None:
            return True
        return release.state == "deployed"

    def handle(self, table, request, obj_ids):
        try:
            result = stx_api.usm.release_commit_req(request, obj_ids)
            messages.success(request, result)
        except Exception as ex:
            messages.error(request, str(ex))

        url = reverse(table.index_url)
        return shortcuts.redirect(url)


class DeployPrecheck(tables.Action):
    name = "deploy-precheck"
    verbose_name = _("Deploy Precheck")

    def allowed(self, request, release=None):
        if release is None:
            return True
        return release.state == "available"

    def single(self, table, request, obj_ids):
        try:
            result = stx_api.usm.deploy_precheck_req(request, obj_ids)
            messages.success(request, result)
        except Exception as ex:
            messages.error(request, str(ex))

        url = reverse(table.index_url)
        return shortcuts.redirect(url)


class DeployStart(tables.Action):
    name = "deploy-start"
    verbose_name = _("Deploy Start")

    def allowed(self, request, release=None):
        if release is None:
            return True
        return release.state == "available"

    def single(self, table, request, obj_id):
        try:
            result = stx_api.usm.deploy_start_req(request, obj_id)
            messages.success(request, result)
        except Exception as ex:
            messages.error(request, str(ex))

        url = reverse(table.index_url)
        return shortcuts.redirect(url)


class DeployActivate(tables.Action):
    name = "deploy-activate"
    verbose_name = _("Deploy Activate")

    def allowed(self, request, release=None):

        valid_states = {
            "host-done",
            "activate-failed"
        }

        if release is None:
            return True
        return (release.state in ["deploying", "removing"] and
                release.deploy_host_state in valid_states)

    def single(self, table, request, obj_id):
        try:
            result = stx_api.usm.deploy_activate_req(request)
            messages.success(request, result)
        except Exception as ex:
            messages.error(request, str(ex))

        url = reverse(table.index_url)
        return shortcuts.redirect(url)


class DeployComplete(tables.Action):
    name = "deploy-complete"
    verbose_name = _("Deploy Complete")

    def allowed(self, request, release=None):
        if release is None:
            return True
        return (release.state in ["removing", "deploying"] and
                release.deploy_host_state == "activate-done")

    def single(self, table, request, obj_id):
        try:
            result = stx_api.usm.deploy_complete_req(request)
            messages.success(request, result)
        except Exception as ex:
            messages.error(request, str(ex))

        url = reverse(table.index_url)
        return shortcuts.redirect(url)


class DeployAbort(tables.Action):
    name = "deploy-abort"
    verbose_name = _("Deploy Abort")

    def allowed(self, request, release=None):

        valid_states = {
            "activate-done",
            "activate",
            "activate-failed",
            "completed",
            "host-done",
            "host-failed",
        }

        if release is None:
            return True
        return (release.state == "deploying" and
                release.deploy_host_state in valid_states)

    def single(self, table, request, obj_id):
        try:
            result = stx_api.usm.deploy_abort_req(request)
            messages.success(request, result)
        except Exception as ex:
            messages.error(request, str(ex))

        url = reverse(table.index_url)
        return shortcuts.redirect(url)


class DeployDelete(tables.Action):
    name = "deploy-delete"
    verbose_name = _("Deploy Delete")

    def allowed(self, request, release=None):

        valid_states = {
            "start-done",
            "start-failed",
            "completed",
            "host-rollback-done",
        }

        if release is None:
            return True
        return (release.state in ["deploying", "removing"] and
                release.deploy_host_state in valid_states)

    def single(self, table, request, obj_id):
        try:
            result = stx_api.usm.deploy_delete_req(request)
            messages.success(request, result)
        except Exception as ex:
            messages.error(request, str(ex))

        url = reverse(table.index_url)
        return shortcuts.redirect(url)


class DeployActivateRollback(tables.Action):
    name = "deploy-activate-rollback"
    verbose_name = _("Deploy Activate Rollback")

    def allowed(self, request, release=None):
        deploy_show = stx_api.usm.deploy_show_req(request)
        if not deploy_show:
            return False

        deploy_show_state = deploy_show[0]['state']
        valid_states = {
            "activate-rollback-failed",
            "activate-rollback-pending",
        }

        if release is None:
            return True

        return (release.state in ["deploying", "removing"] and
                deploy_show_state in valid_states)

    def single(self, table, request, obj_id):
        try:
            result = stx_api.usm.deploy_activate_rollback_req(request)
            messages.success(request, result)
        except Exception as ex:
            messages.error(request, str(ex))

        url = reverse(table.index_url)
        return shortcuts.redirect(url)


class ReleaseFilterAction(tables.FilterAction):
    def filter(self, table, releases, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()

        def comp(release):
            if q in release.release_id.lower():
                return True
            return False

        return list(filter(comp, releases))


class UpdateReleaseRow(tables.Row):
    ajax = True

    def get_data(self, request, release_id):
        release = stx_api.usm.get_release(request, release_id)

        if release is not None and release.state in ["deploying", "removing"]:
            deploy_show_data = stx_api.usm.deploy_show_req(request)
            deploy_host_release = deploy_show_data[0]
            release.deploy_host_state = deploy_host_release[
                'state']

            if release.reboot_required is False:
                release.reboot_required = "N"
            elif release.reboot_required is True:
                release.reboot_required = "Y"

        return release


def get_state_display(release):

    if (release.state in ["deploying", "removing"] and
            hasattr(release, 'deploy_host_state')):
        return f"{release.state} ({release.deploy_host_state})"
    return release.state


class ReleasesTable(tables.DataTable):
    index_url = 'horizon:admin:software_management:index'
    RELEASE_STATE_CHOICES = (
        (None, True),
        ("", True),
        ("none", True),
        ("available", True),
        ("Deployed", True),
        ("Partial-Remove", True),
        ("Applied", True),
        ("Committed", True),
        ("Deploying", True),
        ("Deploying (Start-Done)", True),
        ("Deploying (Start-Failed)", True),
        ("Deploying (Host-Done)", True),
        ("Deploying (Host-Failed)", True),
        ("Deploying (Activate-Done)", True),
        ("Deploying (Activate-Failed)", True),
        ("Deploying (Completed)", True),
        ("Deploying (Activate-Rollback-Pending)", True),
        ("Deploying (Activate-Rollback-Failed)", True),
        ("Deploying (Activate-Rollback-Done)", True),
        ("Deploying (Host-Rollback-Done)", True),
        ("Deploying (Host-Rollback-Failed)", True),
        ("Deploying (Host-Rollback)", True)
    )
    SERVICE_STATE_DISPLAY_CHOICES = (
        ("true", _("Y")),
        ("false", _("N")),
    )
    release_id = tables.Column('release_id',
                               link="horizon:admin:software_management:"
                                    "releasedetail",
                               verbose_name=_('Release'))
    reboot_required = tables.Column(
        'reboot_required',
        verbose_name=_('RR'),
        display_choices=SERVICE_STATE_DISPLAY_CHOICES
    )
    state = tables.Column(get_state_display,
                          verbose_name=_('State'),
                          status=True,
                          status_choices=RELEASE_STATE_CHOICES,
                          classes=['text-capitalize'])
    summary = tables.Column('summary',
                            verbose_name=_('Summary'))

    def get_object_id(self, obj):
        return obj.release_id

    def get_object_display(self, obj):
        return obj.release_id

    class Meta(object):
        name = "releases"
        multi_select = True
        row_class = UpdateReleaseRow
        status_columns = ['state']
        row_actions = (
            DeployPrecheck,
            DeployStart,
            DeployActivate,
            DeployComplete,
            DeployDelete,
            DeleteRelease,
            DeployAbort,
            DeployActivateRollback,
        )
        table_actions = (
            ReleaseFilterAction,
            UploadRelease,
            DeleteRelease,
        )
        verbose_name = _("Release")
        hidden_title = False


class UploadPatch(tables.LinkAction):
    name = "patchupload"
    verbose_name = _("Upload Patches")
    url = "horizon:admin:software_management:patchupload"
    classes = ("ajax-modal", "btn-create")
    icon = "plus"


class ApplyPatch(tables.BatchAction):
    name = "apply"

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Apply Patch",
            "Apply Patches",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Applied Patch",
            "Applied Patches",
            count
        )

    def allowed(self, request, patch=None):
        if patch is None:
            return True
        return patch.repostate == "Available"

    def handle(self, table, request, obj_ids):
        try:
            result = stx_api.patch.patch_apply_req(request, obj_ids)
            messages.success(request, result)
        except Exception as ex:
            messages.error(request, str(ex))

        url = reverse(table.index_url)
        return shortcuts.redirect(url)


class RemovePatch(tables.BatchAction):
    name = "remove"
    classes = ()

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Remove Patch",
            "Remove Patches",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Removed Patch",
            "Removed Patches",
            count
        )

    def allowed(self, request, patch=None):
        if patch is None:
            return True

        if patch.unremovable == "Y":
            if "disabled" not in self.classes:
                self.classes = [c for c in self.classes] + ["disabled"]
        else:
            self.classes = [c for c in self.classes if c != "disabled"]

        return patch.repostate == "Applied"

    def handle(self, table, request, obj_ids):
        try:
            result = stx_api.patch.patch_remove_req(request, obj_ids)
            messages.success(request, result)
        except Exception as ex:
            messages.error(request, str(ex))

        url = reverse(table.index_url)
        return shortcuts.redirect(url)


class DeletePatch(tables.BatchAction):
    name = "delete"
    icon = 'trash'
    action_type = 'danger'

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Delete Patch",
            "Delete Patches",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Deleted Patch",
            "Deleted Patches",
            count
        )

    def allowed(self, request, patch=None):
        if patch is None:
            return True
        return patch.repostate == "Available"

    def handle(self, table, request, obj_ids):
        try:
            result = stx_api.patch.patch_delete_req(request, obj_ids)
            messages.success(request, result)
        except Exception as ex:
            messages.error(request, str(ex))

        url = reverse(table.index_url)
        return shortcuts.redirect(url)


class UpdatePatchRow(tables.Row):
    ajax = True

    def get_data(self, request, patch_id):
        patch = stx_api.patch.get_patch(request, patch_id)
        return patch


class PatchFilterAction(tables.FilterAction):
    def filter(self, table, patches, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()

        def comp(patch):
            if q in patch.patch_id.lower():
                return True
            return False

        return list(filter(comp, patches))


class PatchesTable(tables.DataTable):
    index_url = 'horizon:admin:software_management:index'
    PATCH_STATE_CHOICES = (
        (None, True),
        ("", True),
        ("none", True),
        ("Available", True),
        ("Partial-Apply", True),
        ("Partial-Remove", True),
        ("Applied", True),
        ("Committed", True)
    )

    patch_id = tables.Column('patch_id',
                             link="horizon:admin:software_management:"
                                  "patchdetail",
                             verbose_name=_('Patch ID'))
    reboot_required = tables.Column('reboot_required',
                                    verbose_name=_('RR'))
    sw_version = tables.Column('sw_version',
                               verbose_name=_('Release'))
    patchstate = tables.Column('patchstate',
                               verbose_name=_('Patch State'),
                               status=True,
                               status_choices=PATCH_STATE_CHOICES)
    summary = tables.Column('summary',
                            verbose_name=_('Summary'))

    def get_object_id(self, obj):
        return obj.patch_id

    def get_object_display(self, obj):
        return obj.patch_id

    class Meta(object):
        name = "patches"
        multi_select = True
        row_class = UpdatePatchRow
        status_columns = ['patchstate']
        row_actions = (ApplyPatch, RemovePatch, DeletePatch)
        table_actions = (
            PatchFilterAction, UploadPatch, ApplyPatch, RemovePatch,
            DeletePatch)
        verbose_name = _("Patches")
        hidden_title = False


# Patch Orchestration
def get_cached_strategy(request, strategy_name, table):
    if stx_api.vim.STRATEGY_SW_PATCH == strategy_name:
        if 'patchstrategy' not in table.kwargs:
            table.kwargs['patchstrategy'] = stx_api.vim.get_strategy(
                request, strategy_name)
        return table.kwargs['patchstrategy']
    elif stx_api.vim.STRATEGY_SW_DEPLOY == strategy_name:
        if 'softwaredeploystrategy' not in table.kwargs:
            table.kwargs['softwaredeploystrategy'] = stx_api.vim.get_strategy(
                request, strategy_name)
        return table.kwargs['softwaredeploystrategy']


class CreateStrategy(tables.LinkAction):
    verbose_name = _("Create Strategy")
    classes = ("ajax-modal", "btn-create")
    icon = "plus"

    def allowed(self, request, datum):
        try:
            # Only a single strategy (patch or upgrade) can exist at a time.
            strategy = get_cached_strategy(request,
                                           stx_api.vim.STRATEGY_SW_PATCH,
                                           self.table)
            if not strategy:
                strategy = get_cached_strategy(request,
                                               stx_api.vim.STRATEGY_SW_DEPLOY,
                                               self.table)

            classes = [c for c in self.classes if c != "disabled"]
            self.classes = classes

            if strategy:
                if "disabled" not in self.classes:
                    self.classes = [c for c in self.classes] + ['disabled']
        except Exception as ex:
            LOG.exception(ex)
        return True


class CreatePatchStrategy(CreateStrategy):
    name = "createpatchstrategy"
    url = "horizon:admin:software_management:createpatchstrategy"


class CreateSoftwareDeployStrategy(CreateStrategy):
    name = "create_software_deploy_strategy"
    url = "horizon:admin:software_management:create_software_deploy_strategy"


class DeleteStrategy(tables.Action):
    force = False
    disabled = False
    requires_input = False
    icon = 'trash'
    action_type = 'danger'
    verbose_name = _("Delete Strategy")

    def allowed(self, request, datum):
        try:
            strategy = get_cached_strategy(request, self.strategy_name,
                                           self.table)
            self.disabled = False
            if not strategy or strategy.state in ['aborting', 'applying']:
                self.disabled = True
        except Exception as ex:
            LOG.exception(ex)
        return True

    def get_default_classes(self):
        try:
            if self.disabled:
                return ['disabled']
            return super(DeleteStrategy, self).get_default_classes()
        except Exception as ex:
            LOG.exception(ex)

    def single(self, table, request, obj_id):
        try:
            result = stx_api.vim.delete_strategy(request, self.strategy_name,
                                                 self.force)
            if result:
                messages.success(request, "Strategy Deleted")
            else:
                messages.error(request, "Strategy delete failed")
        except Exception as ex:
            LOG.exception(ex)
            messages.error(request, str(ex))

        url = reverse('horizon:admin:software_management:index')
        return shortcuts.redirect(url)


class DeletePatchStrategy(DeleteStrategy):
    name = "delete_patch_strategy"
    strategy_name = stx_api.vim.STRATEGY_SW_PATCH


class DeleteSoftwareDeployStrategy(DeleteStrategy):
    name = "delete_software_deploy_strategy"
    strategy_name = stx_api.vim.STRATEGY_SW_DEPLOY


class ApplyStrategy(tables.Action):
    requires_input = False
    disabled = False
    verbose_name = _("Apply Strategy")

    def allowed(self, request, datum):
        try:
            strategy = get_cached_strategy(request, self.strategy_name,
                                           self.table)
            self.disabled = False
            if not strategy or strategy.current_phase == 'abort' or \
                    strategy.state in ['build-failed', 'applying',
                                       'applied', 'aborting', 'aborted']:
                self.disabled = True
        except Exception as ex:
            LOG.exception(ex)
        return True

    def get_default_classes(self):
        try:
            if self.disabled:
                return ['disabled']
            return super(ApplyStrategy, self).get_default_classes()
        except Exception as ex:
            LOG.exception(ex)

    def single(self, table, request, obj_id):
        try:
            result = stx_api.vim.apply_strategy(request, self.strategy_name)
            if result:
                messages.success(request, "Strategy apply in progress")
            else:
                messages.error(request, "Strategy apply failed")
        except Exception as ex:
            LOG.exception(ex)
            messages.error(request, str(ex))

        url = reverse('horizon:admin:software_management:index')
        return shortcuts.redirect(url)


class ApplyPatchStrategy(ApplyStrategy):
    name = "apply_patch_strategy"
    strategy_name = stx_api.vim.STRATEGY_SW_PATCH


class ApplySoftwareDeployStrategy(ApplyStrategy):
    name = "apply_software_deploy_strategy"
    strategy_name = stx_api.vim.STRATEGY_SW_DEPLOY


class AbortStrategy(tables.Action):
    requires_input = False
    disabled = False
    action_type = 'danger'
    verbose_name = _("Abort Strategy")
    confirm_message = "You have selected Abort Strategy. " \
                      "Please confirm your selection"

    def allowed(self, request, datum):
        try:
            strategy = get_cached_strategy(request, self.strategy_name,
                                           self.table)
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
            return super(AbortStrategy, self).get_default_classes()
        except Exception as ex:
            LOG.exception(ex)

    def single(self, table, request, obj_id):
        try:
            result = stx_api.vim.abort_strategy(request, self.strategy_name)
            if result:
                messages.success(request, "Strategy abort in progress")
            else:
                messages.error(request, "Strategy abort failed")
        except Exception as ex:
            LOG.exception(ex)
            messages.error(request, str(ex))
        url = reverse('horizon:admin:software_management:index')
        return shortcuts.redirect(url)


class AbortPatchStrategy(AbortStrategy):
    name = "abort_patch_strategy"
    strategy_name = stx_api.vim.STRATEGY_SW_PATCH


class AbortSoftwareDeployStrategy(AbortStrategy):
    name = "abort_software_deploy_strategy"
    strategy_name = stx_api.vim.STRATEGY_SW_DEPLOY


class ApplyStage(tables.BatchAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Apply Stage",
            "Apply Stages",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Applied Stage",
            "Applied Stages",
            count
        )

    def allowed(self, request, stage=None):
        try:
            strategy = get_cached_strategy(request, self.strategy_name,
                                           self.table)
            if stage.result != "initial" or stage.inprogress \
                    or not strategy or strategy.current_phase == 'abort' \
                    or strategy.state in ['aborted', 'aborting']:
                return False
            # Loop through the stages and ensure this is the first in 'line'
            stages = stx_api.vim.get_stages(request, self.strategy_name)
            for s in stages:
                if s.phase.phase_name == stage.phase.phase_name and \
                        s.stage_id == stage.stage_id and \
                        stage.result == 'initial':
                    return True
                if s.result == 'initial' or s.inprogress:
                    return False
        except Exception as ex:
            LOG.exception(ex)
        return False

    def handle(self, table, request, obj_ids):
        for obj_id in obj_ids:
            try:
                stage_id = obj_id.split('-', 1)[1]
                result = stx_api.vim.apply_strategy(request,
                                                    self.strategy_name,
                                                    stage_id)
                if result is None:
                    messages.error(request, "Strategy stage %s apply failed" %
                                   stage_id)
                else:
                    messages.success(request,
                                     "Strategy stage %s apply in progress" %
                                     stage_id)
            except Exception as ex:
                LOG.exception(ex)
                messages.error(request, str(ex))

        url = reverse('horizon:admin:software_management:index')
        return shortcuts.redirect(url)


class ApplyPatchStage(ApplyStage):
    name = "apply_patch_stage"
    strategy_name = stx_api.vim.STRATEGY_SW_PATCH


class ApplySoftwareDeployStage(ApplyStage):
    name = "apply_software_deploy_stage"
    strategy_name = stx_api.vim.STRATEGY_SW_DEPLOY


class AbortStage(tables.BatchAction):
    name = "abort_stage"
    action_type = 'danger'

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            "Abort Stage",
            "Abort Stages",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            "Aborted Stage",
            "Aborted Stages",
            count
        )

    def allowed(self, request, stage=None):
        if not stage:
            return True
        try:
            strategy = get_cached_strategy(request, self.strategy_name,
                                           self.table)
            if not strategy or strategy.current_phase == 'abort' \
                    or strategy.state in ['aborted', 'aborting']:
                return False
        except Exception as ex:
            LOG.exception(ex)
        return stage.inprogress and stage.phase.phase_name == 'apply'

    def handle(self, table, request, obj_ids):
        for obj_id in obj_ids:
            try:
                stage_id = obj_id.split('-', 1)[1]
                result = stx_api.vim.abort_strategy(request,
                                                    self.strategy_name,
                                                    stage_id)
                if result is None:
                    messages.error(request,
                                   "Strategy stage %s abort in progress" %
                                   stage_id)
                else:
                    messages.success(request, "Strategy stage %s aborted" %
                                     stage_id)
            except Exception as ex:
                LOG.exception(ex)
                messages.error(request, str(ex))
        url = reverse('horizon:admin:software_management:index')
        return shortcuts.redirect(url)


class AbortPatchStage(AbortStage):
    name = "abort_patch_stage"
    strategy_name = stx_api.vim.STRATEGY_SW_PATCH


class AbortSoftwareDeployStage(AbortStage):
    name = "abort_software_deploy_stage"
    strategy_name = stx_api.vim.STRATEGY_SW_DEPLOY


def get_current_step_time(stage):
    if stage.current_step >= len(stage.steps):
        return "N/A"
    return get_time(stage.steps[stage.current_step])


def get_time(entity):
    try:
        return datetime.timedelta(seconds=entity.timeout)
    except Exception:
        return "N/A"


def get_current_step_name(stage):
    if stage.current_step >= len(stage.steps):
        return "N/A"
    return stage.steps[stage.current_step].step_name


def get_entities(stage):
    for step in stage.steps:
        if step.step_name == 'sw-patch-hosts':
            return ", ".join(step.entity_names)
        elif step.step_name == 'upgrade-hosts':
            return ", ".join(step.entity_names)
    return "N/A"


FAILURE_STATUSES = ('failed', 'aborted')
STAGE_STATE_CHOICES = (
    (None, True),
    ("", True),
    ("none", True),
    ("success", True),
    ("initial", True),
    ("failed", False),
    ("timed-out", False),
    ("aborted", False),
)


def get_result(stage):
    if stage.phase.phase_name == 'build' and stage.phase.result == 'failed':
        # Special case for build failures
        return stage.phase.result
    if stage.inprogress:
        return "In Progress (Step " + str(stage.current_step + 1) + "/" + \
            str(stage.total_steps) + ")"
    return stage.result


def get_reason(stage):
    if stage.phase.phase_name == 'build' and stage.phase.reason:
        # Special case for build failures
        return stage.phase.reason
    if stage.reason or \
            stage.current_step >= len(stage.steps):
        return stage.reason
    return stage.steps[stage.current_step].reason


def get_phase_name(stage):
    return title(stage.phase.phase_name)


class UpdateStageRow(tables.Row):
    ajax = True

    def get_data(self, request, row_id):
        phase = row_id.split('-', 1)[0]
        stage_id = row_id.split('-', 1)[1]
        stage = stx_api.vim.get_stage(request,
                                      self.strategy_name,
                                      phase,
                                      stage_id)
        return stage


class UpdatePatchStageRow(UpdateStageRow):
    strategy_name = stx_api.vim.STRATEGY_SW_PATCH


class UpdateSoftwareDeployStageRow(UpdateStageRow):
    strategy_name = stx_api.vim.STRATEGY_SW_DEPLOY


class StagesTable(tables.DataTable):
    row_class = UpdateStageRow
    phase = tables.Column(get_phase_name, verbose_name=_('Phase'))
    stage_name = tables.Column('stage_name')
    entities = tables.Column(get_entities, verbose_name=_('Hosts'))
    current_step = tables.Column(get_current_step_name,
                                 verbose_name=_('Current Step Name'))
    step_timeout = tables.Column(get_current_step_time,
                                 verbose_name=_('Current Step Timeout'), )
    status = tables.Column(get_result,
                           status=True,
                           status_choices=STAGE_STATE_CHOICES,
                           verbose_name=_('Status'))
    reason = tables.Column(get_reason,
                           verbose_name=_('Reason'))

    def get_object_id(self, obj):
        return "%s-%s" % (obj.phase.phase_name, obj.stage_id)

    def get_object_display(self, obj):
        return "Stage %s of %s Phase" % (obj.stage_id, obj.phase.phase_name)


def get_patchstage_link_url(stage):
    return reverse("horizon:admin:software_management:patchstagedetail",
                   args=(stage.stage_id, stage.phase.phase_name))


class PatchStagesTable(StagesTable):
    stage_name = tables.Column('stage_name',
                               link=get_patchstage_link_url,
                               verbose_name=_('Stage Name'))

    class Meta(object):
        name = "patchstages"
        multi_select = False
        status_columns = ['status', ]
        row_class = UpdatePatchStageRow
        row_actions = (ApplyPatchStage, AbortPatchStage)
        table_actions = (CreatePatchStrategy, ApplyPatchStrategy,
                         AbortPatchStrategy, DeletePatchStrategy)
        verbose_name = _("Stages")
        hidden_title = False


def get_softwaredeploystage_link_url(stage):
    return reverse(
        "horizon:admin:software_management:softwaredeploystagedetail",
        args=(stage.stage_id, stage.phase.phase_name))


class SoftwareDeployStagesTable(StagesTable):
    stage_name = tables.Column('stage_name',
                               link=get_softwaredeploystage_link_url,
                               verbose_name=_('Stage Name'))

    class Meta(object):
        name = "softwaredeploystages"
        multi_select = False
        status_columns = ['status', ]
        row_class = UpdateSoftwareDeployStageRow
        row_actions = (ApplySoftwareDeployStage, AbortSoftwareDeployStage)
        table_actions = (CreateSoftwareDeployStrategy,
                         ApplySoftwareDeployStrategy,
                         AbortSoftwareDeployStrategy,
                         DeleteSoftwareDeployStrategy)
        verbose_name = _("Stages")
        hidden_title = False


def display_entities(step):
    return ", ".join(step.entity_names)


class UpdateStepRow(tables.Row):
    ajax = True

    def get_data(self, request, row_id):
        phase_name = row_id.split('-', 2)[0]
        stage_id = row_id.split('-', 2)[1]
        step_id = row_id.split('-', 2)[2]
        step = stx_api.vim.get_step(
            request, self.strategy_name, phase_name, stage_id, step_id)
        step.phase_name = phase_name
        step.stage_id = stage_id
        return step


class UpdatePatchStepRow(UpdateStepRow):
    strategy_name = stx_api.vim.STRATEGY_SW_PATCH


class UpdateSoftwareDeployStepRow(UpdateStepRow):
    strategy_name = stx_api.vim.STRATEGY_SW_DEPLOY


class StepsTable(tables.DataTable):
    step_id = tables.Column('step_id', verbose_name=_('Step ID'))
    step_name = tables.Column('step_name', verbose_name=_('Step Name'))
    entities = tables.Column(display_entities, verbose_name=_('Entities'))
    start = tables.Column('start_date_time', verbose_name=_('Start Time'), )
    end = tables.Column('end_date_time', verbose_name=_('End Time'), )
    timeout = tables.Column(get_time, verbose_name=_('Timeout'), )
    result = tables.Column('result',
                           status=True,
                           status_choices=STAGE_STATE_CHOICES,
                           verbose_name=_('Status'))
    reason = tables.Column('reason', verbose_name=_('Reason'))

    def get_object_id(self, obj):
        return "%s-%s-%s" % (obj.phase_name, obj.stage_id, obj.step_id)


class PatchStepsTable(StepsTable):
    class Meta(object):
        name = "steps"
        status_columns = ['result', ]
        row_class = UpdatePatchStepRow
        verbose_name = _("Steps")
        hidden_title = False


class SoftwareDeployStepsTable(StepsTable):
    class Meta(object):
        name = "steps"
        status_columns = ['result', ]
        row_class = UpdateSoftwareDeployStepRow
        verbose_name = _("Steps")
        hidden_title = False

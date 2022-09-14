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
# Copyright (c) 2017-2022 Wind River Systems, Inc.
#

import logging

from dcmanagerclient.api.v1 import client
from dcmanagerclient.exceptions import APIException

from horizon.utils.memoized import memoized  # noqa

from openstack_dashboard.api import base

LOG = logging.getLogger(__name__)


DEFAULT_CONFIG_NAME = "all clouds default"
DEFAULT_GROUP_NAME = "Default"


@memoized
def dcmanagerclient(request):
    endpoint = base.url_for(request, 'dcmanager')
    c = client.Client(project_id=request.user.project_id,
                      user_id=request.user.id,
                      auth_token=request.user.token.id,
                      dcmanager_url=endpoint)
    return c


class Summary(base.APIResourceWrapper):
    _attrs = ['name', 'critical', 'major', 'minor', 'warnings', 'status']


def alarm_summary_list(request):
    summaries = dcmanagerclient(request).alarm_manager.list_alarms()
    return [Summary(summary) for summary in summaries]


class Subcloud(base.APIResourceWrapper):
    _attrs = ['subcloud_id', 'name', 'description', 'location',
              'software_version', 'management_subnet', 'management_state',
              'availability_status', 'deploy_status', 'error_description',
              'management_start_ip', 'management_end_ip',
              'management_gateway_ip', 'systemcontroller_gateway_ip',
              'created_at', 'updated_at', 'group_id', 'sync_status',
              'endpoint_sync_status', ]


def subcloud_list(request):
    subclouds = dcmanagerclient(request).subcloud_manager.list_subclouds()
    return [Subcloud(subcloud) for subcloud in subclouds]


def subcloud_create(request, data):
    return dcmanagerclient(request).subcloud_manager.add_subcloud(
        **data.get('data'))


def subcloud_update(request, subcloud_id, changes):
    response = dcmanagerclient(request).subcloud_manager.update_subcloud(
        subcloud_id, data=changes.get('updated'))
    # Updating returns a list of subclouds for some reason
    return [Subcloud(subcloud) for subcloud in response]


def subcloud_delete(request, subcloud_id):
    return dcmanagerclient(request).subcloud_manager.delete_subcloud(
        subcloud_id)


def subcloud_generate_config(request, subcloud_id, data):
    return dcmanagerclient(request).subcloud_manager.generate_config_subcloud(
        subcloud_id, **data)


# SubCloud Groups functions
class SubcloudGroup(base.APIResourceWrapper):
    _attrs = ['group_id', 'name', 'description', 'update_apply_type',
              'max_parallel_subclouds', 'created_at', 'updated_at', ]


def subcloud_group_create(request, **kwargs):
    response = dcmanagerclient(request).subcloud_group_manager.\
        add_subcloud_group(**kwargs)
    return [SubcloudGroup(subcloud_group) for subcloud_group in response]


def list_subcloud_groups(request):
    subcloud_groups = dcmanagerclient(request).subcloud_group_manager.\
        list_subcloud_groups()
    return [SubcloudGroup(subcloud_g) for subcloud_g in subcloud_groups]


def subcloud_group_get(request, subcloud_group_id):
    response = dcmanagerclient(request).subcloud_group_manager.\
        subcloud_group_detail(subcloud_group_id)
    if response and len(response):
        return SubcloudGroup(response[0])


def subcloud_group_delete(request, subcloud_group_id):
    return dcmanagerclient(request).subcloud_group_manager.\
        delete_subcloud_group(subcloud_group_id)


def subcloud_group_update(request, subcloud_group_id, **kwargs):
    response = dcmanagerclient(request).subcloud_group_manager.\
        update_subcloud_group(subcloud_group_id, **kwargs)
    # Updating returns a list of subclouds groups for some reason
    return [SubcloudGroup(subcloud_group) for subcloud_group in response]


class Strategy(base.APIResourceWrapper):
    _attrs = ['strategy_type', 'subcloud_apply_type',
              'max_parallel_subclouds', 'stop_on_failure', 'state',
              'created_at', 'updated_at']


def get_strategy(request):
    try:
        response = dcmanagerclient(request).sw_strategy_manager.\
            update_sw_strategy_detail()
    except APIException as e:
        if e.error_code == 404:
            return None
        else:
            raise e

    if response and len(response):
        return Strategy(response[0])


def strategy_create(request, data):
    response = dcmanagerclient(request).sw_strategy_manager.\
        create_sw_update_strategy(**data)
    return Strategy(response)


def strategy_apply(request):
    return dcmanagerclient(request).sw_strategy_manager.\
        apply_sw_update_strategy()


def strategy_abort(request):
    return dcmanagerclient(request).sw_strategy_manager.\
        abort_sw_update_strategy()


def strategy_delete(request):
    return dcmanagerclient(request).sw_strategy_manager.\
        delete_sw_update_strategy()


class Step(base.APIResourceWrapper):
    _attrs = ['cloud', 'stage', 'state', 'details', 'started_at',
              'finished_at']


def step_list(request):
    response = dcmanagerclient(request).strategy_step_manager.\
        list_strategy_steps()
    return [Step(step) for step in response]


def step_detail(request, cloud_name):
    response = dcmanagerclient(request).strategy_step_manager. \
        strategy_step_detail(cloud_name)
    return Step(response[0])


class Config(base.APIResourceWrapper):
    _attrs = ['cloud', 'storage_apply_type', 'worker_apply_type',
              'max_parallel_workers', 'alarm_restriction_type',
              'default_instance_action']


def config_list(request):
    response = dcmanagerclient(request).sw_update_options_manager.\
        sw_update_options_list()
    return [Config(config) for config in response]


def config_update(request, subcloud, data):
    response = dcmanagerclient(request).sw_update_options_manager.\
        sw_update_options_update(subcloud, **data)
    return Config(response)


def config_delete(request, subcloud):
    return dcmanagerclient(request).sw_update_options_manager.\
        sw_update_options_delete(subcloud)


def config_get(request, subcloud):
    if subcloud == DEFAULT_CONFIG_NAME:
        subcloud = None
    response = dcmanagerclient(request).sw_update_options_manager.\
        sw_update_options_detail(subcloud)
    if response and len(response):
        return Config(response[0])

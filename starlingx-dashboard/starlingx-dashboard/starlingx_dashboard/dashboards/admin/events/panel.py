#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
#  Copyright (c) 2019-2021 Wind River Systems, Inc.
#
#  SPDX-License-Identifier: Apache-2.0
#

from django.utils.translation import ugettext_lazy as _
import horizon


class Events(horizon.Panel):
    name = _("Events")
    slug = "events"

    def allowed(self, context):
        if context['request'].user.services_region == 'SystemController':
            return False
        else:
            return super(Events, self).allowed(context)

    def nav(self, context):
        if context['request'].user.services_region == 'SystemController':
            return False
        else:
            return True

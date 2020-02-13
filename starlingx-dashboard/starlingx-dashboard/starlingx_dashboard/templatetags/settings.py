#
# Copyright (c) 2020 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.conf import settings
from django import template


register = template.Library()


@register.simple_tag
def is_dc_mode():
    return getattr(settings, 'DC_MODE', False)

#
# Copyright (c) 2020 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django import template

register = template.Library()


@register.filter(name="align_auth_url")
def align_auth_url(url):
    url_list = url.split(':')
    url_list[-1] = '5000'
    return ':'.join(url_list)

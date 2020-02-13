#
# Copyright (c) 2019-2020 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import os

from openstack_dashboard.settings import HORIZON_CONFIG
from openstack_dashboard.settings import ROOT_PATH
from openstack_dashboard.settings import TEMPLATES
from starlingx_dashboard import configss
from tsconfig.tsconfig import distributed_cloud_role


# WEBROOT is the location relative to Webserver root
# should end with a slash.
WEBROOT = '/'

LOCAL_PATH = os.path.dirname(os.path.abspath(__file__))
ALLOWED_HOSTS = ["*"]
HORIZON_CONFIG["password_autocomplete"] = "off"

# The OPENSTACK_HEAT_STACK settings can be used to disable password
# field required while launching the stack.
OPENSTACK_HEAT_STACK = {
    'enable_user_pass': False,
}

OPENSTACK_HOST = "controller"
OPENSTACK_KEYSTONE_URL = "http://%s:5000/v3" % OPENSTACK_HOST
OPENSTACK_API_VERSIONS = {"identity": 3}

OPENSTACK_NEUTRON_NETWORK['enable_distributed_router'] = True  # noqa

# Load Region Config params, if present
# Config OPENSTACK_HOST is still required in region mode since StarlingX
# does not use the local_settings populated via packstack
try:
    if os.path.exists('/etc/openstack-dashboard/region-config.ini'):
        if not configss.CONFSS:
            configss.load('/etc/openstack-dashboard/region-config.ini')

            OPENSTACK_HOST = \
                configss.CONFSS['shared_services']['openstack_host']
            OPENSTACK_KEYSTONE_URL = "http://%s:5000/v3" % OPENSTACK_HOST
            AVAILABLE_REGIONS = [
                (OPENSTACK_KEYSTONE_URL,
                 configss.CONFSS['shared_services']['region_name'])]
            REGION_NAME = configss.CONFSS['shared_services']['region_name']
            SS_ENABLED = "True"
        else:
            SS_ENABLED = "Failed"
    else:
        SS_ENABLED = "False"
except Exception:
    SS_ENABLED = "Exception"

# Change session and CSRF cookie names to prevent login conflict with
# containerized horizon.
# NOTE: These settings break upstream angularJS forms such as the launch
# instance wizard.  If this plugin is to be used in a standard horizon
# deployment these settings must be overwritten to their default values.
CSRF_COOKIE_NAME = 'platformcsrftoken'
SESSION_COOKIE_NAME = 'platformsessionid'

# check if it is in distributed cloud
DC_MODE = False
if distributed_cloud_role and distributed_cloud_role in ['systemcontroller',
                                                         'subcloud']:
    DC_MODE = True

HORIZON_CONFIG["user_home"] = \
    "starlingx_dashboard.utils.settings.get_user_home"

OPENSTACK_ENDPOINT_TYPE = "internalURL"

# Override Django tempory file upload directory
# Directory in which upload streamed files will be temporarily saved. A value
# of `None` will make Django use the operating system's default temporary
# directory
FILE_UPLOAD_TEMP_DIR = "/scratch/horizon"

# Override openstack-dashboard NG_CACHE_TEMPLATE_AGE
NG_TEMPLATE_CACHE_AGE = 300

# Conf file location on CentOS
POLICY_FILES_PATH = "/etc/openstack-dashboard"

# Settings for OperationLogMiddleware
OPERATION_LOG_ENABLED = True
OPERATION_LOG_OPTIONS = {
    'mask_fields': ['password', 'bm_password', 'bm_confirm_password',
                    'current_password', 'confirm_password', 'new_password',
                    'fake_password'],
    'ignore_urls': [],
    'target_methods': ['POST', 'PUT', 'DELETE'],
    'format': ("[%(project_name)s %(project_id)s] [%(user_name)s %(user_id)s]"
               " [%(method)s %(request_url)s %(http_status)s]"
               " parameters:[%(param)s] message:[%(message)s]"),
}

# StarlingX Branding Settings
SITE_BRANDING = "StarlingX"

AVAILABLE_THEMES = [
    ('default', 'Default', 'themes/default'),
    ('material', 'Material', 'themes/material'),
    ('starlingx', 'StarlingX', 'themes/starlingx'),
]
DEFAULT_THEME = 'starlingx'

SELECTABLE_THEMES = [
    ('starlingx', 'StarlingX', 'themes/starlingx'),
]

for root, _dirs, files in os.walk('/opt/branding/applied'):
    if 'manifest.py' in files:
        with open(os.path.join(root, 'manifest.py')) as f:
            code = compile(f.read(), os.path.join(root, 'manifest.py'), 'exec')
            exec(code)

        AVAILABLE_THEMES = [
            ('default', 'Default', 'themes/default'),
            ('material', 'Material', 'themes/material'),
            ('starlingx', 'StarlingX', 'themes/starlingx'),
            ('custom', 'Custom', '/opt/branding/applied'),
        ]
        DEFAULT_THEME = 'custom'

        SELECTABLE_THEMES = [
            ('custom', 'Custom', '/opt/branding/applied'),
        ]


# Add StarlingX templates location to override openstack ones
ADD_TEMPLATE_DIRS = [os.path.join(ROOT_PATH, 'starlingx_templates')]
TEMPLATES[0]['DIRS'] = ADD_TEMPLATE_DIRS + TEMPLATES[0]['DIRS']


STATIC_ROOT = "/www/pages/static"
COMPRESS_OFFLINE = True

# Secure site configuration
SESSION_COOKIE_HTTPONLY = True

# Size of thread batch
THREAD_BATCH_SIZE = 100

try:
    if os.path.exists('/etc/openstack-dashboard/horizon-config.ini'):
        if not configss.CONFSS or 'horizon_params' not in configss.CONFSS:
            configss.load('/etc/openstack-dashboard/horizon-config.ini')

        if configss.CONFSS['horizon_params']['https_enabled'] == 'true':
            CSRF_COOKIE_SECURE = True
            SESSION_COOKIE_SECURE = True
except Exception:
    pass


# Override LOGGING settings
LOGGING['formatters']['standard'] = {  # noqa
    'format':
        '%(levelno)s %(asctime)s [%(levelname)s] %(name)s: %(message)s'
}

LOGGING['formatters']['operation'] = {  # noqa
    # The format of "%(message)s" is defined by
    # OPERATION_LOG_OPTIONS['format']
    'format': '%(asctime)s %(message)s',
}

# Overwrite the console handler to send to syslog
LOGGING['handlers']['console'] = {  # noqa
    'level': 'DEBUG' if DEBUG else 'INFO',  # noqa
    'formatter': 'standard',
    'class': 'logging.handlers.SysLogHandler',
    'facility': 'local7',
    'address': '/dev/log',
}

# Overwrite the operation handler to send to syslog
LOGGING['handlers']['operation'] = {  # noqa
    'level': 'INFO',
    'formatter': 'operation',
    'class': 'logging.handlers.SysLogHandler',
    'facility': 'local7',
    'address': '/dev/log',
}

LOGGING['loggers'].update({  # noqa
    'starlingx_dashboard': {
        'handlers': ['console'],
        'level': 'DEBUG',
        'propagate': False,
    }
})


# Session overrides
SESSION_ENGINE = 'django.contrib.sessions.backends.file'
SESSION_FILE_PATH = '/var/tmp'

# SESSION_TIMEOUT is a method to supersede the token timeout with a shorter
# horizon session timeout (in seconds).  So if your token expires in 60
# minutes, a value of 1800 will log users out after 30 minutes
SESSION_TIMEOUT = 3000

# TOKEN_TIMEOUT_MARGIN ensures the user is logged out before the token
# expires. This parameter specifies the number of seconds before the
# token expiry to log users out. If the token expires in 60 minutes, a
# value of 600 will log users out after 50 minutes.
TOKEN_TIMEOUT_MARGIN = 600


# Retrieve the current system timezone
USE_TZ = True
try:
    tz = os.path.realpath('/etc/localtime')
    TIME_ZONE = tz.split('zoneinfo/')[1]
except Exception:
    TIME_ZONE = 'UTC'

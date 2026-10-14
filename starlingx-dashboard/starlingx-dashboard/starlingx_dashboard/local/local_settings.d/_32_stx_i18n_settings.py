#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import os

import starlingx_dashboard

# Internationalization settings
USE_I18N = True
LANGUAGE_CODE = 'en'

# Restrict the User Settings language selector to the languages actually
# localized for StarlingX, overriding the default list inherited from
# Horizon. Simplified Chinese must use the 'zh-hans' code (catalogs live
# under locale/zh_Hans/); 'zh-cn' has no catalog and silently falls back
# to English.
LANGUAGES = (
    ('en', 'English'),
    ('zh-hans', '简体中文'),
)

# Add the StarlingX dashboard catalogs. Directories in LOCALE_PATHS take
# precedence over the per-app catalogs, which allows overriding Horizon
# translations.
LOCALE_PATHS = [
    os.path.join(os.path.dirname(starlingx_dashboard.__file__), 'locale'),
]

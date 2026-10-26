#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Lock the Horizon i18n settings of the StarlingX dashboard."""

import os
import runpy
import sys
import unittest

from tests.i18n import _helpers


class I18nSettingsTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self._saved_path = list(sys.path)
        sys.path.insert(0, _helpers.PLUGIN_DIR)
        self.addCleanup(self._restore_path)
        self.settings = runpy.run_path(_helpers.SETTINGS_FILE)

    def _restore_path(self):
        sys.path[:] = self._saved_path

    def test_use_i18n_true(self):
        self.assertIs(self.settings['USE_I18N'], True)

    def test_language_code_en(self):
        self.assertEqual('en', self.settings['LANGUAGE_CODE'])

    def test_languages_exactly_en_and_zh_hans(self):
        languages = self.settings['LANGUAGES']
        self.assertEqual(['en', 'zh-hans'], [code for code, _ in languages])
        self.assertEqual({'en': 'English', 'zh-hans': '简体中文'},
                         dict(languages))

    def test_no_zh_cn(self):
        codes = [code for code, _ in self.settings['LANGUAGES']]
        self.assertNotIn('zh-cn', codes)

    def test_locale_paths_point_at_app_locale(self):
        expected = os.path.join(_helpers.APP_DIR, 'locale')
        self.assertEqual([expected], self.settings['LOCALE_PATHS'])
        self.assertTrue(os.path.isdir(expected))

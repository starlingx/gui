#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Lock the Debian build mechanism that compiles the zh_Hans catalogs."""

import os
import re
import shutil
import subprocess
import tempfile
import unittest

from tests.i18n import _helpers

RULES = os.path.join(_helpers.DEBIAN_DIR, 'rules')
CONTROL = os.path.join(_helpers.DEBIAN_DIR, 'control')
INSTALL = os.path.join(_helpers.DEBIAN_DIR, 'starlingx-dashboard.install')
GETTEXT_MAGICS = (b'\x95\x04\x12\xde', b'\xde\x12\x04\x95')


class DebianPackagingStaticTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.rules = _helpers.read_text(RULES)

    def test_build_depends_gettext_and_babel(self):
        stanza = _helpers.control_stanzas(_helpers.read_text(CONTROL))[0]
        self.assertEqual('starlingx-dashboard', stanza['Source'])
        deps = [dep.strip() for dep in stanza['Build-Depends'].split(',')]
        self.assertIn('gettext', deps)
        self.assertIn('python3-babel', deps)

    def test_rules_compiles_both_domains_with_check(self):
        recipe = _helpers.render_recipe(self.rules, '$(LC_DIR)')
        self.assertIn('for d in django djangojs;', recipe)
        self.assertIn('msgfmt --check -o $(LC_DIR)/$d.mo', recipe)
        self.assertNotIn('|| true', recipe)

    def test_rules_installs_into_app_locale_dir(self):
        expected = (
            r'^export DATA_DIR=\$\(ROOT\)/usr/lib/python3/dist-packages$',
            r'^export APP_DIR=\$\(DATA_DIR\)/starlingx_dashboard$',
            r'^export LOCALE_DIR=\$\(APP_DIR\)/locale$',
            r'^export LC_DIR=\$\(LOCALE_DIR\)/zh_Hans/LC_MESSAGES$',
        )
        for pattern in expected:
            self.assertRegex(self.rules, re.compile(pattern, re.M))

    def test_install_file_ships_app_tree(self):
        install = _helpers.read_text(INSTALL).split()
        self.assertIn('usr/lib/python3/dist-packages/starlingx_dashboard/*',
                      install)

    def test_rules_recipe_uses_tab_indent(self):
        lines = _helpers.recipe_lines(self.rules)
        self.assertTrue(lines)
        for line in lines:
            self.assertTrue(line.startswith('\t'), repr(line))

    def test_rules_header_assertion_present(self):
        recipe = _helpers.render_recipe(self.rules, '$(LC_DIR)')
        self.assertIn('nplurals=1; plural=0;', recipe)


@unittest.skipUnless(
    _helpers.have_msgfmt(),
    'msgfmt (gettext) missing; provided by bindep.txt in CI')
class DebianBuildRecipeRunTest(unittest.TestCase):
    """Run the real compile recipe from rules against temp catalog copies."""

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.po_dir = os.path.join(
            self.tmp, 'starlingx_dashboard', 'locale', 'zh_Hans',
            'LC_MESSAGES')
        os.makedirs(self.po_dir)
        for domain in _helpers.DOMAINS:
            shutil.copy(_helpers.po_path(domain), self.po_dir)
        self.out_dir = os.path.join(self.tmp, 'out')

    def _build(self):
        recipe = _helpers.render_recipe(
            _helpers.read_text(RULES), self.out_dir)
        return subprocess.run(['bash', '-c', recipe], cwd=self.tmp,
                              capture_output=True, text=True, check=False)

    def _rewrite(self, domain, func):
        path = os.path.join(self.po_dir, domain + '.po')
        content = _helpers.read_text(path)
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(func(content))

    def test_build_compiles_both_mo_into_locale_dir(self):
        result = self._build()
        self.assertEqual(0, result.returncode, result.stderr)
        for domain in _helpers.DOMAINS:
            mo_file = os.path.join(self.out_dir, domain + '.mo')
            self.assertGreater(os.path.getsize(mo_file), 0)
            with open(mo_file, 'rb') as handle:
                self.assertIn(handle.read(4), GETTEXT_MAGICS)

    def test_broken_po_fails_build(self):
        self._rewrite('django', lambda c: c + '\nmsgid "a"\nmsgstr "b\n')
        result = self._build()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("'django'", result.stderr)

    def test_missing_catalog_fails_build_naming_domain(self):
        os.remove(os.path.join(self.po_dir, 'djangojs.po'))
        result = self._build()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("'djangojs'", result.stderr)

    def test_placeholder_plural_header_fails_build(self):
        self._rewrite('django', lambda c: c.replace(
            _helpers.PLURAL_HEADER, _helpers.PLACEHOLDER_PLURAL_HEADER))
        result = self._build()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("'django'", result.stderr)

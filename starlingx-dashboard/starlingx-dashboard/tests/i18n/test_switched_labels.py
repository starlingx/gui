#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Guard translatability of switched-field labels.

horizon.forms.js replaces a switched field's <label> with the raw value of
its data-<switch>-<value> attribute, both when the dialog opens and on every
toggle. A bare string literal there renders untranslated in any non-English
session and is never extracted into the catalog.
"""

import ast
import os
import re
import unittest

from tests.i18n import _helpers

# Identifiers and control flags; jQuery coerces 'true' to a boolean, so
# these values must never be translated.
CONTROL_KEYS = frozenset((
    'data-switch-on',
    'data-slug',
    'data-required-when-shown',
    'data-hide-on-checked',
))
SWITCH_KEY = re.compile(r'^data-[a-z0-9_]+-[a-z0-9_.-]+$')


def unwrapped_labels(source, filename='<string>'):
    """Return (lineno, key, value) for non-empty literal switch values."""
    found = []
    for node in ast.walk(ast.parse(source, filename=filename)):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if not (isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and SWITCH_KEY.match(key.value)
                    and key.value not in CONTROL_KEYS):
                continue
            # '' is a show/hide marker; a Call such as _() is the fix.
            if (isinstance(value, ast.Constant)
                    and isinstance(value.value, str) and value.value):
                found.append((key.lineno, key.value, value.value))
    return found


class SwitchedLabelsTest(unittest.TestCase):

    def test_detects_bare_literal(self):
        src = "a = {'data-dn_type-vxlan': 'Mode'}\n"
        self.assertEqual([(1, 'data-dn_type-vxlan', 'Mode')],
                         unwrapped_labels(src))

    def test_allows_wrapped_empty_and_control_values(self):
        src = (
            "a = {'data-dn_type-vxlan': _('Mode'),\n"
            "     'data-type-lvm_type': '',\n"
            "     'data-required-when-shown': 'true',\n"
            "     'data-hide-on-checked': 'true',\n"
            "     'data-switch-on': 'dn_type',\n"
            "     'data-slug': 'dn_type'}\n"
        )
        self.assertEqual([], unwrapped_labels(src))

    def test_plugin_has_no_unwrapped_switched_labels(self):
        offenders = []
        for dirpath, _dirs, files in os.walk(_helpers.APP_DIR):
            for name in sorted(files):
                if not name.endswith('.py'):
                    continue
                path = os.path.join(dirpath, name)
                rel = os.path.relpath(path, _helpers.APP_DIR)
                for line, key, value in unwrapped_labels(
                        _helpers.read_text(path), path):
                    offenders.append('%s:%d %s=%r' % (rel, line, key, value))
        self.assertEqual(
            [], sorted(offenders),
            'Wrap these switched-field labels with _():\n'
            + '\n'.join(sorted(offenders)))


if __name__ == '__main__':
    unittest.main()

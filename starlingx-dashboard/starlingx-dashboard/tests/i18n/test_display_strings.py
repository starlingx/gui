#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Guard translatability of Python-side display strings.

A bare literal passed as a display attribute is never extracted into the
catalog and renders in English in any non-English session. ('Name') looks
wrapped but is only a parenthesized string. A page_title is rendered as a
Django template, so _() or a quoted literal inside it is invisible to the
extractor; the fix is page_title = _("Title: {{ obj.name }}").
"""

import ast
import os
import re
import unittest

from tests.i18n import _helpers

DISPLAY_ATTRS = frozenset((
    'verbose_name',
    'verbose_name_plural',
    'label',
    'help_text',
    'empty_value',
))
CHOICE_METHODS = frozenset(('append', 'insert'))
LETTER = re.compile(r'[A-Za-z]')
TEMPLATE_TAG = re.compile(r'{{.*?}}|{%.*?%}', re.S)


def _literal(node):
    """Return the value of a non-empty str constant, else None."""
    if (isinstance(node, ast.Constant) and isinstance(node.value, str)
            and node.value):
        return node.value
    return None


def _target_name(target):
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


def _bad_page_title(value):
    """A literal page_title may only hold template tags with no English."""
    for tag in TEMPLATE_TAG.findall(value):
        if '_(' in tag or '"' in tag or "'" in tag:
            return True
    return bool(LETTER.search(TEMPLATE_TAG.sub('', value)))


def unwrapped_strings(source, filename='<string>'):
    """Return (lineno, kind, value) for untranslatable display strings."""
    found = []
    for node in ast.walk(ast.parse(source, filename=filename)):
        if isinstance(node, ast.keyword) and node.arg in DISPLAY_ATTRS:
            value = _literal(node.value)
            if value is not None:
                found.append((node.value.lineno, node.arg, value))
        elif isinstance(node, ast.Assign):
            value = _literal(node.value)
            if value is None:
                continue
            for target in node.targets:
                name = _target_name(target)
                if name in DISPLAY_ATTRS:
                    found.append((node.lineno, name, value))
                elif name == 'page_title' and _bad_page_title(value):
                    found.append((node.lineno, name, value))
        elif (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in CHOICE_METHODS and node.args
                and isinstance(node.args[-1], ast.Tuple)
                and len(node.args[-1].elts) == 2):
            # (value, label) choice: the label is what the user sees.
            value = _literal(node.args[-1].elts[1])
            if value is not None and LETTER.search(value):
                found.append((node.lineno, 'choice', value))
        elif isinstance(node, ast.List):
            for elt in node.elts:
                if isinstance(elt, ast.Tuple) and len(elt.elts) == 2:
                    value = _literal(elt.elts[1])
                    if value is not None and LETTER.search(value):
                        found.append((elt.lineno, 'choice', value))
    return found


class DisplayStringsTest(unittest.TestCase):

    def test_detects_parenthesized_literal(self):
        src = ("name = tables.Column('name', verbose_name=('Name'))\n"
               "class Meta(object):\n"
               "    verbose_name = (\"Disks\")\n")
        self.assertEqual([(1, 'verbose_name', 'Name'),
                          (3, 'verbose_name', 'Disks')],
                         sorted(unwrapped_strings(src)))

    def test_detects_other_display_attrs(self):
        src = ("f = forms.CharField(label='Type', help_text='Help',\n"
               "                    empty_value='None')\n"
               "field.help_text = 'Pages'\n"
               "class T(object):\n"
               "    verbose_name_plural = 'Disks'\n")
        self.assertEqual(['Disks', 'Help', 'None', 'Pages', 'Type'],
                         sorted(v for _l, _k, v in unwrapped_strings(src)))

    def test_detects_bad_page_titles(self):
        src = ("a = '{{ _(\"Host Detail: \")|add:host.hostname }}'\n"
               "b = 1\n"
               "page_title = '{{ \"Data Network Detail: \"|add:d.name }}'\n"
               "page_title = 'Host Detail'\n")
        self.assertEqual(['page_title', 'page_title'],
                         [k for _l, k, _v in unwrapped_strings(src)])
        src = "page_title = '{{ _(\"Host Detail: \")|add:host.hostname }}'\n"
        self.assertEqual(1, len(unwrapped_strings(src)))

    def test_detects_english_choice_labels(self):
        src = ("choices.append((stor.uuid, 'Collocated with OSD'))\n"
               "choices.insert(0, ('--', '--'))\n"
               "choices = [('default', 'All subclouds')]\n")
        self.assertEqual([(1, 'choice', 'Collocated with OSD'),
                          (3, 'choice', 'All subclouds')],
                         sorted(unwrapped_strings(src)))

    def test_allows_wrapped_empty_and_variable_values(self):
        src = (
            "name = tables.Column('name', verbose_name=_('Name'))\n"
            "f = forms.CharField(label=_('Type'), help_text='',\n"
            "                    empty_value=None)\n"
            "page_title = _('Host Detail: {{ host.hostname }}')\n"
            "page_title = '{{ device.name }}'\n"
            "page_title = '{% if p.name %}{{ p.name }}{% endif %}'\n"
            "choices.append((j.uuid, '%s ' % j.uuid))\n"
            "choices.append((stor.uuid, _('Collocated with OSD')))\n"
            "choices = [('default', _('All subclouds'))]\n"
        )
        self.assertEqual([], unwrapped_strings(src))

    def test_plugin_has_no_unwrapped_display_strings(self):
        offenders = []
        for dirpath, _dirs, files in os.walk(_helpers.APP_DIR):
            for name in sorted(files):
                if not name.endswith('.py'):
                    continue
                path = os.path.join(dirpath, name)
                rel = os.path.relpath(path, _helpers.APP_DIR)
                for line, kind, value in unwrapped_strings(
                        _helpers.read_text(path), path):
                    offenders.append('%s:%d %s=%r' % (rel, line, kind, value))
        self.assertEqual(
            [], sorted(offenders),
            'Wrap these display strings with _():\n'
            + '\n'.join(sorted(offenders)))


if __name__ == '__main__':
    unittest.main()

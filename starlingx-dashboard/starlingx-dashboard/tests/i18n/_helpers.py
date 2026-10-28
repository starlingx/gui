#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Shared helpers for the i18n infrastructure tests."""

import os
import shutil
import subprocess

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
APP_DIR = os.path.join(PLUGIN_DIR, 'starlingx_dashboard')
PO_DIR = os.path.join(APP_DIR, 'locale', 'zh_Hans', 'LC_MESSAGES')
SETTINGS_FILE = os.path.join(
    APP_DIR, 'local', 'local_settings.d', '_32_stx_i18n_settings.py')
DEBIAN_DIR = os.path.normpath(
    os.path.join(PLUGIN_DIR, '..', 'debian', 'all', 'deb_folder'))
DOMAINS = ('django', 'djangojs')

PLURAL_HEADER = '"Plural-Forms: nplurals=1; plural=0;\\n"'
PLACEHOLDER_PLURAL_HEADER = (
    '"Plural-Forms: nplurals=INTEGER; plural=EXPRESSION;\\n"')


def have_msgfmt():
    return shutil.which('msgfmt') is not None


def read_text(path):
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def po_path(domain):
    return os.path.join(PO_DIR, domain + '.po')


def msgfmt_check(po_file, out_file):
    """Run msgfmt exactly as the Debian build does."""
    return subprocess.run(
        ['msgfmt', '--check', '-o', out_file, po_file],
        capture_output=True, text=True, check=False)


def recipe_lines(rules_text):
    """Raw lines of the catalog-compile block of override_dh_install."""
    lines = rules_text.splitlines()
    start = lines.index('override_dh_install:')
    block = []
    collecting = False
    for line in lines[start + 1:]:
        stripped = line.strip()
        if not collecting:
            if stripped.startswith('set -e;'):
                collecting = True
            else:
                continue
        block.append(line)
        if not stripped.endswith('\\'):
            break
    return block


def render_recipe(rules_text, lc_dir):
    """Return the compile recipe as a single shell command line."""
    parts = [line.strip().rstrip('\\').strip()
             for line in recipe_lines(rules_text)]
    recipe = ' '.join(parts)
    return recipe.replace('$(LC_DIR)', lc_dir).replace('$$', '$')


def control_stanzas(control_text):
    """Split a debian/control file into a list of {field: value} dicts."""
    stanzas = []
    in_stanza = False
    last = None
    for line in control_text.splitlines():
        if not line.strip():
            in_stanza = False
            continue
        if line[0] in ' \t':
            stanzas[-1][last] += ' ' + line.strip()
            continue
        if not in_stanza:
            stanzas.append({})
            in_stanza = True
        last, _, value = line.partition(':')
        stanzas[-1][last] = value.strip()
    return stanzas


def package_depends(control_text, package):
    for stanza in control_stanzas(control_text):
        if stanza.get('Package') == package:
            return [dep.strip() for dep in stanza['Depends'].split(',')]
    raise AssertionError('package %s not in control' % package)

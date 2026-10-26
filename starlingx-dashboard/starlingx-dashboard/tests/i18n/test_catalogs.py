#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Lock catalog format validity, structure, CJK font and UTF-8 presence."""

import collections
import glob
import os
import re
import shutil
import tempfile
import unittest

from tests.i18n import _helpers

NEEDS_MSGFMT = unittest.skipUnless(
    _helpers.have_msgfmt(),
    'msgfmt (gettext) missing; provided by bindep.txt in CI')

PRINTF_RE = re.compile(r'%(?:\(\w+\))?[-+ #0]*\d*(?:\.\d+)?[sdifrxX]')
FORMAT_FIELD_RE = re.compile(r'\{\w*\}')
HTML_TAG_RE = re.compile(r'</?\s*(\w+)[^>]*>')
STRING_RE = re.compile(r'^"(.*)"$')
KEYWORD_RE = re.compile(r'^(msgctxt|msgid_plural|msgid|msgstr(?:\[\d+\])?)\s*'
                        r'(".*")?$')


def parse_po(text):
    """Minimal PO parser returning entries as {field: unescaped string}."""
    entries = []
    open_entry = False
    field = None
    for line in text.splitlines():
        if line.startswith('#~'):
            continue
        if not line.strip():
            open_entry = False
            field = None
            continue
        if line.startswith('#'):
            continue
        match = KEYWORD_RE.match(line)
        if match:
            keyword, value = match.groups()
            if not open_entry or (keyword in ('msgctxt', 'msgid') and
                                  'msgid' in entries[-1]):
                entries.append({})
                open_entry = True
            field = keyword
            entries[-1][field] = ''
            line = value or '""'
        if field is None:
            continue
        string = STRING_RE.match(line.strip())
        if string:
            entries[-1][field] += _unescape(string.group(1))
    return entries


def _unescape(value):
    return (value.replace('\\n', '\n').replace('\\t', '\t')
            .replace('\\"', '"').replace('\\\\', '\\'))


def structure(text):
    """Multisets of placeholders and HTML tag names (never the wording)."""
    text = text.replace('%%', '')
    return (collections.Counter(PRINTF_RE.findall(text)),
            collections.Counter(FORMAT_FIELD_RE.findall(text)),
            collections.Counter(HTML_TAG_RE.findall(text)))


def structure_problems(entries):
    problems = []
    for entry in entries:
        msgid = entry.get('msgid')
        if not msgid:
            continue
        for key, value in entry.items():
            if not key.startswith('msgstr') or not value:
                continue
            source = msgid
            if key.startswith('msgstr[') and key != 'msgstr[0]':
                source = entry.get('msgid_plural', msgid)
            if structure(source) != structure(value):
                problems.append('%s: %s' % (key, msgid))
    return problems


def build_po(plural_header, entry='msgid "a"\nmsgstr "b"\n'):
    return (
        'msgid ""\n'
        'msgstr ""\n'
        '"Project-Id-Version: x\\n"\n'
        '"PO-Revision-Date: 2026-01-01 00:00+0000\\n"\n'
        '"Last-Translator: x\\n"\n'
        '"Language-Team: x\\n"\n'
        '"Language: zh_Hans\\n"\n'
        '"MIME-Version: 1.0\\n"\n'
        '"Content-Type: text/plain; charset=UTF-8\\n"\n'
        '"Content-Transfer-Encoding: 8bit\\n"\n'
        + plural_header + '\n\n' + entry)


class ToolchainTest(unittest.TestCase):

    def test_msgfmt_available_when_required(self):
        if os.environ.get('STX_I18N_REQUIRE_MSGFMT') != '1':
            self.skipTest('STX_I18N_REQUIRE_MSGFMT not set')
        self.assertTrue(_helpers.have_msgfmt(),
                        'msgfmt (gettext) is required; see bindep.txt')


@NEEDS_MSGFMT
class PluralFormsMsgfmtGateTest(unittest.TestCase):
    """msgfmt --check, as invoked by the Debian build, gates Plural-Forms."""

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _check(self, plural_header):
        po_file = os.path.join(self.tmp, 'x.po')
        with open(po_file, 'w', encoding='utf-8') as handle:
            handle.write(build_po(plural_header))
        return _helpers.msgfmt_check(po_file, os.path.join(self.tmp, 'x.mo'))

    def test_placeholder_plural_forms_header_fails_msgfmt_check(self):
        result = self._check(_helpers.PLACEHOLDER_PLURAL_HEADER)
        self.assertNotEqual(0, result.returncode, result.stderr)

    def test_placeholder_expression_only_fails(self):
        result = self._check('"Plural-Forms: nplurals=1; plural=EXPRESSION;'
                             '\\n"')
        self.assertNotEqual(0, result.returncode, result.stderr)

    def test_valid_zh_plural_forms_header_passes(self):
        result = self._check(_helpers.PLURAL_HEADER)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(os.path.isfile(os.path.join(self.tmp, 'x.mo')))


class SeededCatalogTest(unittest.TestCase):

    @NEEDS_MSGFMT
    def test_seeded_catalogs_pass_msgfmt_check(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        for domain in _helpers.DOMAINS:
            result = _helpers.msgfmt_check(
                _helpers.po_path(domain), os.path.join(tmp, domain + '.mo'))
            self.assertEqual(0, result.returncode, result.stderr)

    def test_seeded_header_plural_forms_zh(self):
        for domain in _helpers.DOMAINS:
            text = _helpers.read_text(_helpers.po_path(domain))
            self.assertIn('"Plural-Forms: nplurals=1; plural=0;', text)

    def test_placeholder_and_html_structure_preserved(self):
        for domain in _helpers.DOMAINS:
            entries = parse_po(_helpers.read_text(_helpers.po_path(domain)))
            self.assertTrue(entries)
            self.assertEqual([], structure_problems(entries), domain)

    def test_plural_entries_have_nplurals_msgstr_count(self):
        for domain in _helpers.DOMAINS:
            entries = parse_po(_helpers.read_text(_helpers.po_path(domain)))
            for entry in entries:
                if 'msgid_plural' not in entry:
                    continue
                forms = sorted(k for k in entry if k.startswith('msgstr['))
                self.assertEqual(['msgstr[0]'], forms, entry['msgid'])

    def test_parser_detects_placeholder_mismatch(self):
        entries = parse_po('msgid "Hi %(name)s"\nmsgstr "Hi %(nome)s"\n')
        self.assertEqual(1, len(structure_problems(entries)))
        entries = parse_po('msgid "Hi %(name)s"\nmsgstr "Hi %(name)s"\n')
        self.assertEqual([], structure_problems(entries))

    def test_parser_detects_html_mismatch(self):
        entries = parse_po('msgid "<b>x</b>"\nmsgstr "x"\n')
        self.assertEqual(1, len(structure_problems(entries)))
        entries = parse_po('msgid "<b>x</b>"\nmsgstr "<b>y</b>"\n')
        self.assertEqual([], structure_problems(entries))

    def test_parser_handles_plural_and_continuations(self):
        entries = parse_po(
            'msgid "%d item"\nmsgid_plural "%d "\n"items"\n'
            'msgstr[0] "%d x"\n')
        self.assertEqual('%d items', entries[0]['msgid_plural'])
        self.assertEqual([], structure_problems(entries))


class FontAndUtf8Test(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.control = _helpers.read_text(
            os.path.join(_helpers.DEBIAN_DIR, 'control'))

    def test_cjk_font_in_runtime_depends(self):
        deps = _helpers.package_depends(self.control, 'starlingx-dashboard')
        self.assertIn('fonts-wqy-zenhei', deps)

    def test_font_not_only_in_build_depends(self):
        source = _helpers.control_stanzas(self.control)[0]
        self.assertNotIn('fonts-wqy-zenhei', source['Build-Depends'])

    def test_error_page_declares_utf8(self):
        page = os.path.join(_helpers.APP_DIR, 'themes', 'starlingx',
                            'templates', '500.html')
        self.assertIn('charset=utf-8', _helpers.read_text(page).lower())

    def test_catalog_headers_declare_utf8(self):
        for domain in _helpers.DOMAINS:
            text = _helpers.read_text(_helpers.po_path(domain))
            self.assertIn('charset=utf-8', text.lower())

    def test_no_non_utf8_default_charset_override(self):
        pattern = os.path.join(os.path.dirname(_helpers.SETTINGS_FILE), '*.py')
        for path in glob.glob(pattern):
            for match in re.finditer(r'^DEFAULT_CHARSET\s*=\s*(.+)$',
                                     _helpers.read_text(path), re.M):
                self.assertRegex(match.group(1).lower(), r'utf-?8', path)

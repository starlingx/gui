#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Guard translatability of template text.

Three template patterns cannot be translated into natural Chinese:

* ``{{ "Total: " }}`` is a Django string literal. It never goes through
  gettext, so it renders in English in every language.
* ``{% trans "There are " %}{{ n }}{% trans " alarms" %}`` splits one
  sentence around a value. A translator cannot reorder the pieces.
* A ``{% blocktrans %}`` whose body holds markup puts HTML in the msgid
  (and, when it spans a tag boundary, can render the same value twice).

The fix is one ``{% trans %}`` per label and one ``{% blocktrans %}`` per
sentence with named placeholders, with markup, ``<br>``, spacing and units
outside the msgid.
"""
import os
import re
import unittest

from tests.i18n import _helpers

LETTER = re.compile(r'[A-Za-z]')
ENTITY = re.compile(r'&[A-Za-z]+;|&#\d+;')
BREAK = re.compile(r'<br\s*/?>', re.I)

# {{ "literal" }}; a literal that only holds spacing, markup, punctuation, a
# unit or a boolean is not display text.
LITERAL_VARIABLE = re.compile(r'{{\s*(["\'])(.*?)\1\s*}}', re.S)
UNITS = frozenset(('MiB', 'GiB', 'MB', 'GB', 'kiB/s', 'B'))
BOOLEANS = frozenset(('True', 'False'))

_TRANS = r'{%\s*trans(?:late)?\s+(?:"[^"]*"|\'[^\']*\')\s*%}'
# A sentence cut around a value: {% trans "a" %}{{ v }}{% trans "b" %}.
# The look-ahead reports overlapping pairs, as in "a" v "b" w "c".
FRAGMENT = re.compile(r'(?=(' + _TRANS + r'\s*{{[^}]*}}\s*' + _TRANS + r'))')

BLOCKTRANS = re.compile(
    r'{%\s*blocktrans(?:late)?\b[^%]*%}(.*?){%\s*endblocktrans(?:late)?\s*%}',
    re.S)
MARKUP = re.compile(r'>|<[A-Za-z/!]')

# INFRA-10 Ceph pool quota sentence: its span ids are read by the live total
# script, so the markup has to stay inside the msgid.
BLOCKTRANS_ALLOWED = ('id="total_quota"', 'id="total_tier_size"')

TEMPLATE_DIRS = ('/templates/', '/starlingx_templates/')


def _line(text, offset):
    return text.count('\n', 0, offset) + 1


def display_literals(text):
    """Return (line, literal) for {{ "English" }} used as UI text."""
    found = []
    for match in LITERAL_VARIABLE.finditer(text):
        core = BREAK.sub('', ENTITY.sub('', match.group(2))).strip()
        if not LETTER.search(core):
            continue
        if core in UNITS or core in BOOLEANS:
            continue
        found.append((_line(text, match.start()), match.group(2)))
    return found


def split_sentences(text):
    """Return (line, text) for trans / value / trans fragments."""
    return [(_line(text, m.start(1)), ' '.join(m.group(1).split()))
            for m in FRAGMENT.finditer(text)]


def markup_in_blocktrans(text):
    """Return (line, body) for blocktrans bodies that hold markup."""
    found = []
    for match in BLOCKTRANS.finditer(text):
        body = match.group(1)
        if not MARKUP.search(body):
            continue
        if any(marker in body for marker in BLOCKTRANS_ALLOWED):
            continue
        found.append((_line(text, match.start()), ' '.join(body.split())))
    return found


def template_files():
    for dirpath, _dirs, files in os.walk(_helpers.APP_DIR):
        norm = dirpath.replace(os.sep, '/') + '/'
        if not any(part in norm for part in TEMPLATE_DIRS):
            continue
        for name in sorted(files):
            if name.endswith('.html'):
                yield os.path.join(dirpath, name)


class TemplateStringsTest(unittest.TestCase):

    def test_detects_string_literals(self):
        src = ('<strong>{{ "Total: " }}</strong>\n'
               '{{ "&nbsp;&nbsp;Pending: "}}\n'
               "{{ 'Size:&nbsp;' }}\n")
        self.assertEqual([(1, 'Total: '), (2, '&nbsp;&nbsp;Pending: '),
                          (3, 'Size:&nbsp;')], display_literals(src))

    def test_allows_markup_spacing_units_and_booleans(self):
        src = ('{{ "<br>" }} {{ "<br/>" }} {{ " MiB" }} {{ " GiB " }}\n'
               '{{ "&nbsp;" }} {{ ": " }} {{ "False" }} {{ "True" }}\n'
               '{{ " kiB/s " }} {{ "" }}\n')
        self.assertEqual([], display_literals(src))

    def test_ignores_variables_and_filters(self):
        src = ('{{ memory.total }} {{ x|default:"None" }}\n'
               '{{ x|add:"text" }}\n')
        self.assertEqual([], display_literals(src))

    def test_detects_split_sentences(self):
        src = ('<p>{% trans "There are " %}{{ n }}'
               '{% trans " alarms, " %}{{ m }}{% trans " bad." %}</p>\n'
               '{% trans "a" %}\n {{ v }}\n {% trans "b" %}\n')
        self.assertEqual([1, 1, 2],
                         [line for line, _text in split_sentences(src)])

    def test_allows_labels_next_to_values(self):
        src = ('{% trans "Total" %}: {{ n }}\n'
               '{% trans "a" %} {% trans "b" %}\n'
               '{% trans "a" as t %}{{ t }}{% trans "b" as u %}\n'
               '{% blocktrans %}{{ n }} alarms.{% endblocktrans %}\n')
        self.assertEqual([], split_sentences(src))

    def test_detects_markup_in_blocktrans(self):
        src = ('{% blocktrans %}<p>{{ a }} GiB Used</p>{% endblocktrans %}\n'
               '{% blocktrans with a=b %}x {{ a }}">{{ a }}'
               '{% endblocktrans %}\n'
               '{% blocktranslate trimmed %}\n <b>x</b>\n'
               '{% endblocktranslate %}\n')
        self.assertEqual([1, 2, 3],
                         [line for line, _body in markup_in_blocktrans(src)])

    def test_allows_plain_blocktrans_and_ceph_sentence(self):
        src = ('{% blocktrans with a=b %}{{ a }} GiB of {{ b }}'
               '{% endblocktrans %}\n'
               '{% blocktrans %}<span id="total_quota">{{ q }}</span> GiB'
               '{% endblocktrans %}\n')
        self.assertEqual([], markup_in_blocktrans(src))

    def test_plugin_templates_are_translatable(self):
        offenders = []
        for path in template_files():
            rel = os.path.relpath(path, _helpers.APP_DIR)
            text = _helpers.read_text(path)
            for line, value in display_literals(text):
                offenders.append('%s:%d literal %r' % (rel, line, value))
            for line, value in split_sentences(text):
                offenders.append('%s:%d fragment %r' % (rel, line, value))
            for line, value in markup_in_blocktrans(text):
                offenders.append('%s:%d blocktrans %r' % (rel, line, value))
        self.assertEqual(
            [], sorted(offenders),
            'Use {% trans %} per label and one {% blocktrans %} per sentence'
            ' with named placeholders:\n' + '\n'.join(sorted(offenders)))


if __name__ == '__main__':
    unittest.main()

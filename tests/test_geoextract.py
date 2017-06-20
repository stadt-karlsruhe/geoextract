#!/usr/bin/env python
# encoding: utf-8

# Copyright (c) 2016-2017, Stadt Karlsruhe (www.karlsruhe.de)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import re

import mock

from geoextract import *


class TestNameExtractor(object):
    '''
    Test ``geoextract.NameExtractor``.
    '''
    def setup(self):
        self.ex = NameExtractor()
        self.names = ['foo', 'foobar', 'a space', 'öüä']
        pipeline = mock.Mock(normalized_names=self.names)
        self.ex.setup(pipeline)

    def check(self, s, expected):
        assert list(self.ex.extract(s)) == expected

    def test_match_at_string_start(self):
        '''
        Test matches at the beginning of the string.
        '''
        for name in self.names:
            self.check(name + ' x', [(0, len(name), {'name': name})])

    def test_match_at_string_end(self):
        '''
        Test matches at the end of the string.
        '''
        for name in self.names:
            self.check('x ' + name, [(2, len(name), {'name': name})])

    def test_match_inside_string(self):
        '''
        Test matches in the middle of the string.
        '''
        for name in self.names:
            self.check('x ' + name + ' y', [(2, len(name), {'name': name})])

    def test_match_complete_string(self):
        '''
        Test matching the complete string.
        '''
        for name in self.names:
            self.check(name, [(0, len(name), {'name': name})])

    def test_word_only_matches(self):
        '''
        Test that only complete words are matched.
        '''
        self.check('xfoo xfooy foox', [])


class TestWindowExtractor(object):
    '''
    Test ``geoextract.WindowExtractor``.
    '''
    def check_windows(self, text, start_len=2, stop_len=3):
        windows = []
        class DummyExtractor(WindowExtractor):
            def _window_extract(self, window):
                windows.append(window)
                return []
        list(DummyExtractor(start_len, stop_len).extract(text))
        return windows

    def check_results(self, text, start_len=2, stop_len=3):
        class DummyExtractor(WindowExtractor):
            def _window_extract(self, window):
                yield {'name': window}
        return list(DummyExtractor(start_len, stop_len).extract(text))

    def test_leading_and_trailing_whitespace(self):
        '''
        Test leading and trailing whitespace is ignored.
        '''
        assert self.check_windows('  a b c') == ['a b', 'b c', 'a b c']
        assert self.check_windows('a b c  ') == ['a b', 'b c', 'a b c']
        assert self.check_windows('  a b c  ') == ['a b', 'b c', 'a b c']

    def test_whitespace_collapse(self):
        '''
        Test that whitespace between words is collapsed.
        '''
        assert self.check_windows('a  b\tc\nd') == ['a b', 'b c', 'c d',
                                                    'a b c', 'b c d']

    def test_single_width(self):
        '''
        Test windows of a single width.
        '''
        assert self.check_windows('a b c', 1, 1) == ['a', 'b', 'c']
        assert self.check_windows('a b c', 2, 2) == ['a b', 'b c']
        assert self.check_windows('a b c', 3, 3) == ['a b c']

    def test_match_meta_data(self):
        '''
        Test meta-data of matches.
        '''
        assert self.check_results('a b c d') == [
            (0, 3, {'name': 'a b'}),
            (2, 3, {'name': 'b c'}),
            (4, 3, {'name': 'c d'}),
            (0, 5, {'name': 'a b c'}),
            (2, 5, {'name': 'b c d'}),
        ]


class TestPatternExtractor(object):
    '''
    Test ``geoextract.PatternExtractor``.
    '''
    def extract(self, text, patterns, start_len=1, stop_len=4):
        extractor = PatternExtractor(patterns, start_len, stop_len)
        return list(extractor.extract(text))

    def test_compiled_regex(self):
        '''
        Test using a compiled regex as input.
        '''
        assert self.extract('a', [re.compile(r'(?P<a>a)')]) == [
            (0, 1, {'a': 'a'})
        ]

    def test_multiple_patterns(self):
        '''
        Test passing multiple patterns.
        '''
        patterns = [r'(?P<a>^a$)', r'(?P<b>^b$)', r'(?P<c>^c$)']
        assert self.extract('a b c', patterns) == [
            (0, 1, {'a': 'a'}),
            (2, 1, {'b': 'b'}),
            (4, 1, {'c': 'c'}),
        ]

    def test_missing_optional_matches(self):
        '''
        Test that optional, not matched patterns are ignored.
        '''
        assert self.extract('a', [r'(?P<a>a)(?P<b>b)*']) == [
            (0, 1, {'a': 'a'})
        ]

    def test_windows(self):
        '''
        Test that matching is done using windows.
        '''
        assert self.extract('a a a a', [r'(?P<a>[a ]+)']) == [
            (0, 1, {'a': 'a'}),
            (2, 1, {'a': 'a'}),
            (4, 1, {'a': 'a'}),
            (6, 1, {'a': 'a'}),
            (0, 3, {'a': 'a a'}),
            (2, 3, {'a': 'a a'}),
            (4, 3, {'a': 'a a'}),
            (0, 5, {'a': 'a a a'}),
            (2, 5, {'a': 'a a a'}),
            (0, 7, {'a': 'a a a a'}),
        ]


class TestNameValidator(object):
    '''
    Test ``geoextract.NameValidator``.
    '''
    FIELDS = ['street', 'city']

    def create_validator(self, *locations):
        v = NameValidator()
        locations = {loc['name']: loc for loc in locations}
        pipeline = mock.Mock(locations=locations)
        v.setup(pipeline)
        return v

    def test_unknown_location(self):
        '''
        Test unknown locations.
        '''
        v = self.create_validator()
        for field in self.FIELDS:
            assert not v.validate({field: 'unknown'})

    def test_known_location_unknown_type(self):
        '''
        Test known locations with unknown type.
        '''
        v = self.create_validator({'name': 'no-type'})
        for field in self.FIELDS:
            assert not v.validate({field: 'no-type'})

    def test_known_location_wrong_type(self):
        '''
        Test known locations with a wrong type.
        '''
        v = self.create_validator({'name': 'wrong-type', 'type': 'wrong'})
        for field in self.FIELDS:
            assert not v.validate({field: 'wrong-type'})

    def test_known_location_correct_type(self):
        '''
        Test known locations with a wrong type.
        '''
        for field in self.FIELDS:
            v = self.create_validator({'name': 'correct-type', 'type': field})
            assert v.validate({field: 'correct-type'})

    def test_named_location(self):
        '''
        Test that locations with a name are always accepted.
        '''
        v = self.create_validator({'name': 'no-type'},
                                  {'name': 'wrong-type', 'type': 'wrong'})
        for field in self.FIELDS:
            assert v.validate({'name': 'a name', field: 'no-type'})
            assert v.validate({'name': 'a name', field: 'wrong-type'})


class TestBasicNormalizer(object):
    '''
    Test ``geoextract.BasicNormalizer``.
    '''
    def check(self, s, expected, **kwargs):
        n = BasicNormalizer(**kwargs)
        assert n.normalize(s) == expected

    def test_stemming(self):
        '''
        Test stemming in different languages.
        '''
        self.check('streets', 'street', stem='english')
        self.check('streets', 'streets', stem=False)
        self.check('orte', 'ort', stem='german')
        self.check('orte', 'orte', stem=False)

    def test_to_ascii(self):
        '''
        Test conversion to ASCII.
        '''
        self.check('öüäß', 'ouass', to_ascii=True)
        self.check('öüäß', 'öüäß', to_ascii=False)

    def test_rejoin_lines(self):
        '''
        Test re-joining of lines split by a hyphen.
        '''
        for s, joined, not_joined in [
            ('foo-\nbar', 'foobar', 'foo bar'),
            ('foo- \nbar', 'foobar', 'foo bar'),
            ('foo -\nbar', 'foo bar', 'foo bar'),
            ('foo\n-bar', 'foo bar', 'foo bar'),
            ('foo\nbar', 'foo bar', 'foo bar'),
            ('1-\n2', '1-2', '1 2'),
        ]:
            self.check(s, joined, rejoin_lines=True)
            self.check(s, not_joined, rejoin_lines=False)

    def test_remove_hyphens(self):
        '''
        Test removal of hyphens.
        '''
        for s, removed, not_removed in [
            ('foo-bar', 'foobar', 'foo bar'),
            ('f-o-o-b-a-r', 'foobar', 'f o o b a r'),
            ('1-2', '1-2', '1-2'),
            ('1-2-3', '1-2-3', '1-2-3'),
            ('2000-3000', '2000-3000', '2000-3000'),
        ]:
            self.check(s, removed, remove_hyphens=True)
            self.check(s, not_removed, remove_hyphens=False)

    def test_remove_specials(self):
        '''
        Test removal of special characters.
        '''
        for s, removed in [
            ('hello?', 'hello'),
            ('!hello', 'hello'),
            ('foo!?#bar', 'foo bar'),
            ('#f!$o?/o+', 'f o o'),
            ('2.3', '2.3'),
            ('-2.3', '-2.3'),
            ('-2.3e-34', '-2.3e-34'),
            ('1234-', '1234-'),
            ('1+2', '1+2'),
            ('+134', '+134'),
        ]:
            self.check(s, removed, remove_specials=True)
            self.check(s, s, remove_specials=False)

    def test_substitutions(self):
        '''
        Test substitutions.
        '''
        for s, subs, expected in [
            ('foob', [(r'b\b', 'bar')], 'foobar'),
            ('ab', [(r'a', 'A'), (r'b', 'B')], 'AB'),
        ]:
            self.check(s, expected, subs=subs)
            self.check(s, s, subs=[])

    def test_whitespace_collapse(self):
        '''
        Test collapse of whitespace.
        '''
        self.check(' \n \r \t a \n \r \t b \n \r \t ', 'a b')


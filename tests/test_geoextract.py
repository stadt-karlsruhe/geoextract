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

'''
Tests for the geoextract module.
'''


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import re

import mock

import geoextract
from . import sort_as_json


class TestNameExtractor(object):
    '''
    Test ``geoextract.NameExtractor``.
    '''

    def setup(self):  # noqa: D102
        self.ex = geoextract.NameExtractor()
        self.names = ['foo', 'foobar', 'a space', 'öüä']
        pipeline = mock.Mock(normalized_names=self.names)
        self.ex.setup(pipeline)

    def _check(self, s, expected):
        assert list(self.ex.extract(s)) == expected

    def test_match_at_string_start(self):
        '''
        Test matches at the beginning of the string.
        '''
        for name in self.names:
            self._check(name + ' x', [(0, len(name), {'name': name})])

    def test_match_at_string_end(self):
        '''
        Test matches at the end of the string.
        '''
        for name in self.names:
            self._check('x ' + name, [(2, len(name), {'name': name})])

    def test_match_inside_string(self):
        '''
        Test matches in the middle of the string.
        '''
        for name in self.names:
            self._check('x ' + name + ' y', [(2, len(name), {'name': name})])

    def test_match_complete_string(self):
        '''
        Test matching the complete string.
        '''
        for name in self.names:
            self._check(name, [(0, len(name), {'name': name})])

    def test_word_only_matches(self):
        '''
        Test that only complete words are matched.
        '''
        self._check('xfoo xfooy foox', [])

    def test_no_locations(self):
        '''
        Test that the extractor works with an empty list of locations.
        '''
        extractor = geoextract.NameExtractor()
        pipeline = geoextract.Pipeline([], extractors=[extractor])
        assert pipeline.extract('foobar') == []


class TestWindowExtractor(object):
    '''
    Test ``geoextract.WindowExtractor``.
    '''

    def _check_windows(self, text, start_len=2, stop_len=3):
        windows = []

        class DummyExtractor(geoextract.WindowExtractor):
            def _window_extract(self, window):
                windows.append(window)
                return []

        list(DummyExtractor(start_len, stop_len).extract(text))
        return windows

    def _check_results(self, text, start_len=2, stop_len=3):

        class DummyExtractor(geoextract.WindowExtractor):
            def _window_extract(self, window):
                yield {'name': window}

        return list(DummyExtractor(start_len, stop_len).extract(text))

    def test_leading_and_trailing_whitespace(self):
        '''
        Test leading and trailing whitespace is ignored.
        '''
        assert self._check_windows('  a b c') == ['a b', 'b c', 'a b c']
        assert self._check_windows('a b c  ') == ['a b', 'b c', 'a b c']
        assert self._check_windows('  a b c  ') == ['a b', 'b c', 'a b c']

    def test_whitespace_collapse(self):
        '''
        Test that whitespace between words is collapsed.
        '''
        assert self._check_windows('a  b\tc\nd') == ['a b', 'b c', 'c d',
                                                     'a b c', 'b c d']

    def test_single_width(self):
        '''
        Test windows of a single width.
        '''
        assert self._check_windows('a b c', 1, 1) == ['a', 'b', 'c']
        assert self._check_windows('a b c', 2, 2) == ['a b', 'b c']
        assert self._check_windows('a b c', 3, 3) == ['a b c']

    def test_match_meta_data(self):
        '''
        Test meta-data of matches.
        '''
        assert self._check_results('a b c d') == [
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

    def extract(self, text, patterns, start_len=1, stop_len=4):  # noqa: D102
        extractor = geoextract.PatternExtractor(patterns, start_len, stop_len)
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

    def _create_validator(self, *locations):
        v = geoextract.NameValidator()
        locations = {loc['name']: loc for loc in locations}
        pipeline = mock.Mock(locations=locations)
        v.setup(pipeline)
        return v

    def test_unknown_location(self):
        '''
        Test unknown locations.
        '''
        v = self._create_validator()
        for field in self.FIELDS:
            assert not v.validate({field: 'unknown'})

    def test_known_location_unknown_type(self):
        '''
        Test known locations with unknown type.
        '''
        v = self._create_validator({'name': 'no-type'})
        for field in self.FIELDS:
            assert not v.validate({field: 'no-type'})

    def test_known_location_wrong_type(self):
        '''
        Test known locations with a wrong type.
        '''
        v = self._create_validator({'name': 'wrong-type', 'type': 'wrong'})
        for field in self.FIELDS:
            assert not v.validate({field: 'wrong-type'})

    def test_known_location_correct_type(self):
        '''
        Test known locations with a wrong type.
        '''
        for field in self.FIELDS:
            v = self._create_validator({'name': 'correct-type', 'type': field})
            assert v.validate({field: 'correct-type'})

    def test_named_location(self):
        '''
        Test that locations with a name are always accepted.
        '''
        v = self._create_validator({'name': 'no-type'},
                                   {'name': 'wrong-type', 'type': 'wrong'})
        for field in self.FIELDS:
            assert v.validate({'name': 'a name', field: 'no-type'})
            assert v.validate({'name': 'a name', field: 'wrong-type'})


class TestBasicNormalizer(object):
    '''
    Test ``geoextract.BasicNormalizer``.
    '''

    def _check(self, s, expected, **kwargs):
        n = geoextract.BasicNormalizer(**kwargs)
        assert n.normalize(s) == expected

    def test_stemming(self):
        '''
        Test stemming in different languages.
        '''
        self._check('streets', 'street', stem='english')
        self._check('streets', 'streets', stem=False)
        self._check('orte', 'ort', stem='german')
        self._check('orte', 'orte', stem=False)

    def test_to_ascii(self):
        '''
        Test conversion to ASCII.
        '''
        self._check('öüäß', 'ouass', to_ascii=True)
        self._check('öüäß', 'öüäß', to_ascii=False)

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
            self._check(s, joined, rejoin_lines=True)
            self._check(s, not_joined, rejoin_lines=False)

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
            self._check(s, removed, remove_hyphens=True)
            self._check(s, not_removed, remove_hyphens=False)

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
            self._check(s, removed, remove_specials=True)
            self._check(s, s, remove_specials=False)

    def test_substitutions(self):
        '''
        Test substitutions.
        '''
        for s, subs, expected in [
            ('foob', [(r'b\b', 'bar')], 'foobar'),
            ('ab', [(r'a', 'A'), (r'b', 'B')], 'AB'),
        ]:
            self._check(s, expected, subs=subs)
            self._check(s, s, subs=[])

    def test_whitespace_collapse(self):
        '''
        Test collapse of whitespace.
        '''
        self._check(' \n \r \t a \n \r \t b \n \r \t ', 'a b')


class TestKeyFilterPostprocessor(object):
    '''
    Test ``geoextract.KeyFilterPostprocessor``.
    '''

    def test_postprocess(self):
        '''
        Test the postprocessing.
        '''
        kfp = geoextract.KeyFilterPostprocessor(['a', 'b'])
        for location, expected in [
            ({}, {}),
            ({'c': 1}, {}),
            ({'c': 1, 'd': 2}, {}),
            ({'a': 1}, {'a': 1}),
            ({'b': 1}, {'b': 1}),
            ({'a': 1, 'b': 2}, {'a': 1, 'b': 2}),
            ({'a': 1, 'c': 2}, {'a': 1}),
            ({'b': 1, 'c': 2}, {'b': 1}),
            ({'a': 1, 'b': 2, 'c': 3}, {'a': 1, 'b': 2}),
        ]:
            assert kfp.postprocess(location) == expected


def debug_string(s):
    '''
    Format a string for debugging output.
    '''
    if not s:
        return '<empty>'
    parts = []
    for c in s:
        if c == ' ':
            parts.append('.')
        elif c == '\t':
            parts.append('#')
        elif c == '\n':
            parts.append('\\\n')
        else:
            parts.append(c)
    return ''.join(parts)


def deline(s):
    '''
    Remove empty leading and trailing lines.
    '''
    lines = s.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return '\n'.join(lines)


def _dedent(lines, start, direction):
    current = start
    try:
        while True:
            candidate = lines[0][current]
            if candidate not in [' ', '\t']:
                return current
            for line in lines[1:]:
                if line[current] != candidate:
                    return current
            else:
                current += direction
    except IndexError:
        return current


def double_dedent(s):
    '''
    Strip common leading and trailing whitespace from lines of a string.
    '''
    lines = s.splitlines()
    prefix = _dedent(lines, 0, 1)
    postfix = _dedent(lines, -1, -1)
    print((prefix, postfix))
    if postfix < -1:
        return '\n'.join(line[prefix:postfix + 1] for line in lines)
    else:
        return '\n'.join(line[prefix:] for line in lines)


class TestWhitespaceSplitter(object):
    '''
    Test ``geoextract.WhitespaceSplitter``.
    '''

    def _check(self, s, expected, margin=None):
        kwargs = {}
        if margin:
            kwargs['margin'] = margin
        splitter = geoextract.WhitespaceSplitter(**kwargs)
        result = sorted(double_dedent(deline(chunk))
                        for chunk in splitter.split(s))
        expected = [double_dedent(deline(e)) for e in expected]
        try:
            assert result == expected
        except AssertionError:
            print('Result:\n')
            for r in result:
                print('{}\n'.format(debug_string(r)))
            print('\nExpected:\n')
            for e in expected:
                print('{}\n'.format(debug_string(e)))
            raise

    def test_padding(self):
        '''
        Test rectangular padding of chunks.
        '''
        self._check('''
            xxx   y
            x     y
            x   yyyyy
            x     y
            xxx   y
        ''', [
            '''
              y  
              y  
            yyyyy
              y  
              y  
            ''',  # noqa
            '''
            xxx
            x  
            x  
            x  
            xxx
            '''  # noqa
        ], margin=(1, 1))

    def test_overlapping(self):
        '''
        Test overlapping chunks.
        '''
        self._check('''
            x yyyyyyyy
            x y      y
            x y xxxx y
            x y    x y
            x yyyy x y
            x      x y
            xxxxxxxx y
        ''', [
            '''
            x       
            x       
            x   xxxx
            x      x
            x      x
            x      x
            xxxxxxxx
            ''',  # noqa
            '''
            yyyyyyyy
            y      y
            y      y
            y      y
            yyyy   y
                   y
                   y
            '''

        ], margin=(1, 1))

    def test_margins(self):
        '''
        Test different margins.
        '''
        s = '''
            aaa bb  c

            eee ff  g


            iii jj  k
        '''
        for margin, expected in [
            (
                (1, 1),
                ['aaa', 'bb', 'c', 'eee', 'ff', 'g', 'iii', 'jj', 'k']
            ),
            (
                (2, 1),
                ['aaa bb', 'c', 'eee ff', 'g', 'iii jj', 'k']
            ),
            (
                (3, 1),
                ['aaa bb  c', 'eee ff  g', 'iii jj  k']
            ),
            (
                (1, 2),
                ['aaa\n   \neee', 'bb\n  \nff', 'c\n \ng', 'iii', 'jj', 'k']
            ),
            (
                (1, 3),
                ['aaa\n   \neee\n   \n   \niii', 'bb\n  \nff\n  \n  \njj',
                 'c\n \ng\n \n \nk']
            ),
            (
                (2, 2),
                ['aaa bb\n      \neee ff', 'c\n \ng', 'iii jj', 'k']
            ),
            (
                (2, 3),
                ['aaa bb\n      \neee ff\n      \n      \niii jj',
                 'c\n \ng\n \n \nk']
            ),
            (
                (3, 3),
                ['aaa bb  c\n' +
                 '         \n' +
                 'eee ff  g\n' +
                 '         \n' +
                 '         \n' +
                 'iii jj  k']
            ),
        ]:
            self._check(s, expected, margin)

    def test_empty(self):
        '''
        Test empty string as input argument.
        '''
        self._check('', [])

    def test_only_whitespace(self):
        '''
        Test whitespace-only inputs.
        '''
        for s in [' ', '\t', '\n', ' \t \n \n\t\n   \n']:
            self._check(s, [])


class UpperNormalizer(geoextract.Normalizer):
    '''
    Normalizer that converts text to upper-case.
    '''

    def normalize(self, s):  # noqa: D102
        return s.upper()


location1 = {'name': 'foo'}
location2 = {'name': 'bar', 'aliases': ['bazinga']}


class FakeExtractor(geoextract.Extractor):
    '''
    Fake extractor that returns hard-coded results.
    '''

    def __init__(self, results):
        '''
        Constructor.

        ``results`` is the hard-coded result that should be returned by
        ``extract``.
        '''
        self.results = results

    def extract(self, s):  # noqa: D102
        for result in self.results:
            yield result


def subsets(items):
    '''
    Returns a list of all subsets of an iterable.
    '''
    subsets = [[]]
    for item in items:
        subsets += [subset + [item] for subset in subsets]
    return subsets


class TestPipeline(object):
    '''
    Test ``geoextract.Pipeline``.
    '''

    def test_component_setup(self):
        '''
        Test that components are setup correctly.
        '''
        normalizer = mock.Mock()
        extractor1 = mock.Mock()
        extractor2 = mock.Mock()
        validator = mock.Mock()
        splitter = mock.Mock()
        postprocessor1 = mock.Mock()
        postprocessor2 = mock.Mock()
        geoextract.Pipeline([], extractors=[extractor1, extractor2],
                            validator=validator, normalizer=normalizer,
                            splitter=splitter, postprocessors=[postprocessor1,
                            postprocessor2])
        assert normalizer.setup.called
        assert extractor1.setup.called
        assert extractor2.setup.called
        assert validator.setup.called
        assert splitter.setup.called
        assert postprocessor1.setup.called
        assert postprocessor2.setup.called

    def test_locations(self):
        '''
        Test that locations are correctly converted to a dict.
        '''
        pipeline = geoextract.Pipeline([location1, location2])
        locations = pipeline.locations
        assert locations['foo'] is location1
        assert locations['bar'] is location2
        assert len(locations) == 2

    def test_normalized_names(self):
        '''
        Test that location names are correctly normalized.
        '''
        pipeline = geoextract.Pipeline([location1, location2],
                                       normalizer=UpperNormalizer())
        names = pipeline.normalized_names
        assert names['FOO'] is location1
        assert names['BAR'] is location2
        assert names['BAZINGA'] is location2
        assert len(names) == 3

    def test_normalized_extractor_input(self):
        '''
        Test that extractor input is normalized.
        '''
        extractor = mock.Mock()
        extractor.extract = mock.Mock()
        extractor.extract.return_value = []
        pipeline = geoextract.Pipeline([], extractors=[extractor],
                                       normalizer=UpperNormalizer())
        pipeline.extract('foo')
        extractor.extract.assert_called_once_with('FOO')

    def test_no_normalizer(self):
        '''
        Test disabled normalization.
        '''
        extractor = mock.Mock()
        extractor.extract = mock.Mock()
        extractor.extract.return_value = [(0, 1, {'name': 'A  B'})]
        pipeline = geoextract.Pipeline([{'name': 'A  B'}],
                                       extractors=[extractor],
                                       normalizer=False)
        results = pipeline.extract('NO_NORMALIZATION--')
        extractor.extract.assert_called_once_with('NO_NORMALIZATION--')
        assert results == [{'name': 'A  B'}]

    def test_name_denormalization(self):
        '''
        Test that names in results are denormalized.
        '''
        locations = [
            {'name': 'a-street'},
            {'name': 'a-city'},
            {'name': 'a-name'},
        ]
        normalizer = UpperNormalizer()
        result = (0, 0, {'name': 'A-NAME', 'street': 'A-STREET',
                  'city': 'A-CITY'})
        pipeline = geoextract.Pipeline(locations, normalizer=normalizer,
                                       extractors=[FakeExtractor([result])])
        extracted = pipeline.extract('does not matter')
        assert extracted[0]['name'] == 'a-name'
        assert extracted[0]['street'] == 'a-street'
        assert extracted[0]['city'] == 'a-city'

    def test_extractors(self):
        '''
        Test that extractors are called correctly.
        '''
        extractor1 = FakeExtractor([(0, 1, {'name': 'foo'})])
        extractor2 = FakeExtractor([(1, 1, {'name': 'bar'})])
        pipeline = geoextract.Pipeline([], extractors=[extractor1, extractor2])
        results = pipeline.extract('does not matter')
        assert sorted(r['name'] for r in results) == ['bar', 'foo']

    def test_pruning_of_overlapping_results(self):
        '''
        Test that overlapping results are pruned.
        '''
        # a
        #  bb
        #   c
        #   ddd
        #  eeee
        #      ff
        #     gg
        extractor = FakeExtractor([
            (0, 1, {'name': 'a'}),
            (1, 2, {'name': 'b'}),
            (2, 1, {'name': 'c'}),
            (2, 3, {'name': 'd'}),
            (1, 4, {'name': 'e'}),
            (5, 2, {'name': 'f'}),
            (4, 2, {'name': 'g'}),
        ])
        pipeline = geoextract.Pipeline([], extractors=[extractor])
        results = pipeline.extract('does not matter')
        assert sorted(r['name'] for r in results) == ['a', 'e', 'f', 'g']

    def test_duplicate_removal(self):
        '''
        Test removal of duplicate results.
        '''
        keys = ['street', 'house_number', 'postcode', 'city']
        for subkeys in subsets(keys):
            subkeys.append('name')
            loc1 = {subkey: subkey for subkey in subkeys}
            loc2 = loc1.copy()  # Equal to loc1
            loc3 = loc1.copy()
            loc3['foo'] = 'bar'  # Equal to loc1 because other keys are ignored
            loc4 = loc1.copy()
            loc4[subkeys[0]] = 'x'  # Not equal
            extractor = FakeExtractor([
                (0, 1, loc1),
                (1, 1, loc2),
                (2, 1, loc3),
                (3, 1, loc4),
            ])
            pipeline = geoextract.Pipeline([], extractors=[extractor])
            results = pipeline.extract('does not matter')
            assert sort_as_json(results) == sort_as_json([loc1, loc4])

    def test_validation(self):
        '''
        Test validation of results.
        '''
        class MockValidator(geoextract.Validator):
            def validate(self, location):
                return location['name'] == 'a'

        extractor = FakeExtractor([
            (0, 1, {'name': 'a'}),
            (1, 1, {'name': 'b'}),
        ])
        pipeline = geoextract.Pipeline([], extractors=[extractor],
                                       validator=MockValidator())
        results = pipeline.extract('does not matter')
        assert len(results) == 1
        assert results[0]['name'] == 'a'

    def test_no_validation(self):
        '''
        Test disabled validation.
        '''
        extractor = FakeExtractor([(0, 1, {'name': 'a'})])
        pipeline = geoextract.Pipeline([], extractors=[extractor],
                                       validator=False)
        assert pipeline.extract('does not matter') == [{'name': 'a'}]

    def test_postprocessing(self):
        '''
        Test postprocessing of results.
        '''
        class MockPostprocessor(geoextract.Postprocessor):
            def postprocess(self, location):
                if location['name'] == 'a':
                    location['foo'] = 'bar'
                    return location
                else:
                    return False

        extractor = FakeExtractor([
            (0, 1, {'name': 'a'}),
            (1, 1, {'name': 'b'}),
        ])
        pipeline = geoextract.Pipeline([], extractors=[extractor],
                                       postprocessors=[MockPostprocessor()])
        results = pipeline.extract('does not matter')
        assert len(results) == 1
        assert results[0] == {'name': 'a', 'foo': 'bar'}

    def test_splitting(self):
        '''
        Test splitting of documents.
        '''
        class MockSplitter(geoextract.Splitter):
            def split(self, s):
                return s

        extractor = mock.Mock()
        extractor.extract = mock.Mock()
        extractor.extract.return_value = []
        pipeline = geoextract.Pipeline([], extractors=[extractor],
                                       splitter=MockSplitter())
        pipeline.extract('foo')
        extractor.extract.assert_has_calls(
            [mock.call('f'), mock.call('o'), mock.call('o')]
        )

    def test_no_splitting(self):
        '''
        Test disabled splitting.
        '''
        extractor = mock.Mock()
        extractor.extract = mock.Mock()
        extractor.extract.return_value = []
        pipeline = geoextract.Pipeline([], extractors=[extractor],
                                       splitter=False)
        pipeline.extract('white   space')
        extractor.extract.assert_called_once_with('white space')

    def test_app_creation(self):
        '''
        Test creating a web app from a pipeline.
        '''
        pipeline = geoextract.Pipeline([])
        app = pipeline.create_app()
        assert hasattr(app, 'run')

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

import mock

from geoextract import *


class TestNameExtractor(object):
    '''
    Test ``geoextract.NameExtractor.
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


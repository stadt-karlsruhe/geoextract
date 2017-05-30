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
Utilities for splitting text into parts.
'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import numpy as np
from scipy.ndimage.measurements import find_objects, label
from scipy.ndimage.morphology import binary_dilation


def _string_to_array(s):
    '''
    Convert a string to a NumPy array.

    Returns a 2D NumPy array where array rows correspond to lines in the
    string. Shorter lines are padded with zeros to get a rectangular
    shape.
    '''
    lines = s.splitlines()
    if not lines:
        return np.empty((0, 0))
    m = len(lines)
    n = max(len(line) for line in lines)
    a = np.zeros((m, n), dtype=np.int32)
    for i, line in enumerate(lines):
        for j, char in enumerate(line):
            a[i, j] = ord(char)
    return a


class WhitespaceSplitter(object):
    '''
    Splits a string into connected parts of non-whitespace.

    Two characters in ``text`` belong to the same parts if they aren't
    separated by a space (either vertically or horizontally). By
    default, parts are separated horizontally by two spaces and
    vertically by a single space. Hence, the following image shows 6
    components (where ``.`` represents a space)::

        a.b..c
        a.b..c
        ......
        d.e..f
        ......
        ......
        g.h..i

    You change the number of spaces required to separate parts
    vertically and horizontally via the constructor's ``margin``
    parameter. For example, for ``margin=(1, 1)`` the image above yields
    9 parts, because the previously connected ``a``/``b`` and ``d`/``e``
    parts are not connected anymore. Similarly, ``margin=(2, 2)`` yields
    4 parts and``margin=(3, 3)`` yields a single part for the whole
    text.
    '''
    def __init__(self, margin=(2, 1)):
        '''
        Constructor.

        ``margin`` is a pair of integers which determine how many spaces
        are required to separate parts horizontally and vertically.
        '''
        self.margin = margin

    def split(self, text):
        '''
        Split a text into parts.
        '''
        a = _string_to_array(text)
        if not a.size:
            return []
        b = np.copy(a)
        b[b == ord(' ')] = 0
        if self.margin != (1, 1):
            # Dilate the image
            structure = np.zeros((2 * (self.margin[1] - 1) + 1,
                                  2 * (self.margin[0] - 1) + 1))
            structure[self.margin[1] - 1:, self.margin[0] - 1:] = 1
            labels = binary_dilation(b, structure=structure).astype(b.dtype)
        else:
            labels = b
        num = label(labels, structure=np.ones((3, 3)), output=labels)
        objects = find_objects(labels)
        parts = []
        for i, obj in enumerate(objects):
            mask = labels[obj] != i + 1
            region = np.copy(a[obj])
            region[mask] = ord(' ')
            part = '\n'.join(''.join(unichr(c or ord(' ')) for c in row)
                             for row in region.tolist())
            parts.append(part)
        return parts


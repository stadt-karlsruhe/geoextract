#!/usr/bin/env python
# encoding: utf-8

'''
Extraction of locations from free-form text.

This library tries to extract locations (e.g. postal addresses, street
names, POI names) from free-form/unstructured text. It is intended for
geo-referencing existing documents.
'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import itertools
import re

import ahocorasick


# From the (old) itertools docs, see
# http://stackoverflow.com/a/6822773/857390
def windowed(seq, n=2):
    '''
    Sliding window over an iterable.
    '''
    it = iter(seq)
    result = tuple(itertools.islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result


def split(s):
    '''
    Split a string at whitespace.

    Works like ``str.split`` but returns a list of tuples `(pos, part)`
    where `part` is the sub-string and `pos` its index in the original
    string.
    '''
    parts = []
    pos = None
    for m in re.finditer(r'\s+', s):
        if pos is not None:
            parts.append((pos, s[pos:m.start()]))
        pos = m.end()
    if pos < len(s):
        parts.append((pos, s[pos:]))
    return parts


class PatternExtractor(object):
    '''
    Extractor for regular expression matches.

    Many forms of addresses follow fixed patterns, which can be
    expressed using regular expressions. This class provides an
    extractor for pattern-based location candidates.

    Its main advantage is its support for scanning a text in overlapping
    windows of a varying number of space-separated words. This solves a
    problem caused by names (of roads, cities, ...) containing spaces:
    For example, in the text ``"We meet at 7 Bay Road in the morning"``,
    a space-accepting regular expression might end up matching not only
    ``Bay Road`` but ``Bay Road in the`` or more. To avoid this problem,
    the text is scanned multiple times in windows of space-separated
    words of varying length::

        We meet               #
        meet at               #
        ...                   # groups of 2 words
        in the                #
        the morning           #

        We meet at            #
        meet at 7             #
        ...                   # groups of 3 words
        Road in the           #
        in the morning        #

        We meet at 7          #
        meet at 7 Bay         #
        ...                   #  groups of 4 words
        Bay Road in the       #
        Road in the morning   #

        ...

    You can change the minimum and maximum group size via the
    constructor arguments ``start_len`` and ``stop_len``.
    '''
    def __init__(self, patterns, start_len=2, stop_len=7):
        '''
        Constructor.

        ``patterns`` is a list of *compiled* regular expression objects.
        Each of these must include named groups. The names of the groups
        are used by ``extract`` to build the result dict.

        ``start_len`` and ``stop_len`` specify the minimum and maximimum
        (both inclusive) number of space-separated words in the sliding
        windows. Unless you're matching single words using your patterns
        you shouldn't reduce ``start_len`` (a fast way of extracting
        fixed strings is provided by ``NameExtractor``). The value of
        ``stop_len`` should match the maximum number of space-separated
        components that you expect in your locations. For example, if
        you're looking for locations of the form ``<name> + <number>``
        and ``name`` may contain up to 3 spaces then set ``stop_len=4``
        to check windows with up to 4 words.
        '''
        self.patterns = patterns
        self.start_len = start_len
        self.stop_len = stop_len

    def extract(self, text):
        '''
        Extract potential locations using regular expressions.

        Yields all matches for the patterns (as given to the constructor) in
        ``text``. Each match is reported as a 3-tuple ``(start, length,
        match)``, where ``start`` is the start index of the match in
        ``text``, ``length`` is its length in characters and ``match`` is a
        dict that contains the values of the named groups of the pattern.
        '''
        words = split(text)
        for length in range(self.start_len, self.stop_len + 1):
            for start, window in enumerate(windowed(words, length)):
                s = ' '.join(w[1] for w in window)
                for pattern in self.patterns:
                    m = pattern.search(s)
                    if m:
                        yield (window[0][0], len(s), m.groupdict())


def filter_results(results):
    '''
    Prune overlapping results.

    If the text region of a result is covered by another result then the
    smaller result is dropped. That way, for each location in the text
    only the longest (and hopefully most complete) result is kept.
    '''
    if not results:
        return []
    # Sort increasingly by start and decreasingly by length
    results = sorted(results, key=lambda x: (x[0], -x[1]))
    keep = [results[0]]
    for result in results[1:]:
        if (result[0] + result[1]) > (keep[-1][0] + keep[-1][1]):
            keep.append(result)
    return keep


def unique_dicts(dicts):
    '''
    Remove duplicates from a list of dicts.
    '''
    return [dict(s) for s in set(frozenset(d.items()) for d in dicts)]


class NameExtractor(object):
    '''
    Fast extractor for fixed strings.

    During geo-extraction one often wants to find all occurrences of a
    large list of strings in a given text (e.g. the names of points of
    interest). However, doing this naively takes very long. This class
    provides a fast alternative using Aho-Corasick automata.

    It is intended to be used in combination with ``pattern_extract``.
    '''
    def __init__(self, names):
        '''
        Constructor.

        ``names`` is a list of names.
        '''
        # Build an Aho-Corasick automaton for fast name search.
        # Unfortunately, the `ahocorasick` module currently doesn't
        # support Unicode on Python 2, so we have to do some manual
        # encoding/decoding. We also add a space at the start and end to
        # avoid finding parts of words. That of course assumes that other
        # word delimiters have been converted to spaces during
        # normalization.
        self._automaton = ahocorasick.Automaton()
        for name in names:
            b = (' ' + name + ' ').encode('utf-8')
            self._automaton.add_word(b, name)
        self._automaton.make_automaton()

    def extract(self, text):
        '''
        Extract names from a text.

        Yields tuples ``(start, length, match)`` where ``start`` is the
        start index of the name in ``text``, ``length`` is the length of
        the name and ``match`` is ``{'name': name}``.
        '''
        b = text.encode('utf-8')
        for end_index, name in self._automaton.iter(b):
            end_index -= 2  # Because of space-padding
            end_index = len(b[:end_index + 1].decode('utf-8'))
            length = len(name)
            yield (end_index - length + 1, length, {'name': name})


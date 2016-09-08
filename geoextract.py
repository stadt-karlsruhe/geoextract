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


def pattern_extract(text, patterns, validate, start_len=2, stop_len=7):
    '''
    Extract locations using regular expressions.

    ``text`` is a free-form text that may contain one or more locations.
    Location candidates are extracted from ``text`` using ``patterns``,
    which contains a list of *compiled* regular expression objects. Each
    of these patterns should include several named groups. For each
    match of a pattern in ``text``, the captured groups are extracted
    into a dictionary which is then passed to ``validate``.

    The idea is that the regular expressions express the expected forms
    of locations (i.e. their syntax) while ``validate`` checks whether
    they make sense (for example by comparing an extracted street name
    with a list of known names).

    ``pattern_extract`` returns a list with all matches for which
    ``validate`` returned a true value. Each match is returned as a
    tuple ``(start, length, match)``, where ``start`` is the start index
    of the match in ``text``, ``length`` is its length in characters and
    ``match`` is the dict that was passed to ``validate``.

    Since the names in locations can contain spaces care has to be taken
    to avoid the regular expressions matching too many space-separated
    words. For example, in the text ``"We meet at 7 Bay Road in the
    morning"`` a space-accepting regular expression might end up
    matching not only ``Bay Road`` but ``Bay Road in the`` or more. To
    avoid this problem, the text is scanned multiple times in groups of
    space-separated words of varying length::

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

    You can change the minimum and maximum group size via ``start_len``
    (inclusive) and ``stop_len`` (exclusive).
    '''
    results = []
    words = split(text)
    for length in range(start_len, stop_len):
        for start, window in enumerate(windowed(words, length)):
            s = ' '.join(w[1] for w in window)
            for pattern in patterns:
                m = pattern.search(s)
                if m:
                    result = m.groupdict()
                    if validate(result):
                        results.append((window[0][0], len(s), result))
    return results


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


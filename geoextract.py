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

from postal.parser import parse_address


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


def sublist_index(big, small, start=0):
    '''
    Find a small list in a big list.
    '''
    while True:
        start = big.index(small[0], start, len(big) - len(small) + 1)
        if big[start:start + len(small)] == small:
            return start
        start += 1


def sublist_indices(big, small, start=0, overlapping=True):
    '''
    Find all occurrences of a small list in a big list.
    '''
    while True:
        try:
            start = sublist_index(big, small, start)
        except ValueError:
            break
        yield start
        if overlapping:
            start += 1
        else:
            start += len(small)


def extract(text, validate, names=None, start_len=2, stop_len=6):
    results = []
    words = text.split()

    # Address extraction via libpostal
    for length in range(start_len, stop_len):
        for start, window in enumerate(windowed(words, length)):
            result = parse_address(' '.join(window))
            result = dict((key, value) for (value, key) in result)
            if not validate(result):
                continue
            results.append((start, length, result))

    # Name extraction
    for name in (names or []):
        name_words = name.split()
        for index in sublist_indices(words, name_words):
            results.append((index, len(name_words), {'name': name}))

    # Remove incomplete matches. The idea is that if a match is contained
    # within another match then it is dropped. That way, for each location
    # in the text, only the longest (and hopefully most complete) match
    # is kept.
    if results:
        # Sort increasingly by start and decreasingly by length
        results = sorted(results, key=lambda x: (x[0], -x[1]))
        keep = [results[0]]
        for result in results[1:]:
            if (result[0] + result[1]) > (keep[-1][0] + keep[-1][1]):
                keep.append(result)
        results = keep

    # Remove duplicates
    return [dict(s) for s in set(frozenset(r[2].items()) for r in results)]



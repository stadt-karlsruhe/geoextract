#!/usr/bin/env python
# encoding: utf-8

# Copyright (c) 2016, Stadt Karlsruhe (www.karlsruhe.de)
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


__version__ = '0.1.0'


# From the (old) itertools docs, see
# http://stackoverflow.com/a/6822773/857390
def _windowed(seq, n=2):
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


def _split(s):
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



def unique_dicts(dicts):
    '''
    Remove duplicates from a list of dicts.
    '''
    return [dict(s) for s in set(frozenset(d.items()) for d in dicts)]


class Extractor(object):
    '''
    Base class for extractors.
    '''
    def extract(self, text):
        '''
        Extract potential locations from a text.

        ``text`` is the plain text to extract locations from.

        Yields tuples ``(start, length, data)`` where ``start`` is the
        start index of the location in ``text``, ``length`` is the
        length of the match and ``data`` is a dict with information
        about the location.

        This method is implemented by the various subclasses, which look
        for different types of locations and hence return different
        values in ``data``.
        '''
        raise NotImplementedError('Must be implemented in subclasses.')


class NameExtractor(Extractor):
    '''
    Fast extractor for fixed strings.

    During geo-extraction one often wants to find all occurrences of a
    large list of strings in a given text (e.g. the names of points of
    interest). However, doing this naively takes very long. This class
    provides a fast alternative using Aho-Corasick automata.

    To avoid finding matches inside words only words surrounded by
    spaces (or at the beginning and end of the text) are matched.
    '''
    def __init__(self):
        '''
        Constructor.
        '''
        self._automaton = None  # Initialized by ``setup``

    def setup(self, pipeline):
        # Build an Aho-Corasick automaton for fast name search.
        # Unfortunately, the `ahocorasick` module currently doesn't
        # support Unicode on Python 2, so we have to do some manual
        # encoding/decoding. We also add a space at the start and end to
        # avoid finding parts of words. That of course assumes that other
        # word delimiters have been converted to spaces during
        # normalization.
        self._automaton = ahocorasick.Automaton()
        for name in pipeline.normalized_names:
            name = name.strip()
            b = (' ' + name + ' ').encode('utf-8')
            self._automaton.add_word(b, name)
        self._automaton.make_automaton()

    def extract(self, text):
        # Pad with spaces and encode, see __init__
        b = (' ' + text + ' ').encode('utf-8')
        for end_index, name in self._automaton.iter(b):
            end_index -= 1  # Because of space-padding of key
            end_index = len(b[1:end_index + 1].decode('utf-8')) - 1
            length = len(name)  # ``name`` is the original Unicode name
            yield (end_index - length + 1, length, {'name': name})


class WindowExtractor(Extractor):
    '''
    Base class for extractors based on sliding windows.

    A common problem when extracting potential locations from a text is
    that names of streets and cities often contain spaces. Faced with a
    sequence of words, the extractor then has to decide how many of them
    may belong to a name. This often leads to matches which contain too
    many words. For example, in the text ``"We meet at 7 Bay Road in the
    morning"``, we might end up matching not only ``Bay Road`` but ``Bay
    Road in the`` or more. While such overly long matches can often be
    quickly eliminated during validation they potentially prevent
    shorter, correct matches from being registered at all.

    To avoid this problem, subclasses of this class scan the text
    multiple times using windows of a varying number of space-separated
    words:

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

    This ensures that shorter combinations also have the chance of being
    matched. Obviously this doesn't prevent the incorrect longer groups
    of being matched, too. As mentioned before those need to be
    eliminated in a second validation step.

    You can change the minimum and maximum group size via the
    constructor arguments ``start_len`` and ``stop_len``.
    '''
    def __init__(self, start_len, stop_len):
        '''
        Constructor.

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
        self.start_len = start_len
        self.stop_len = stop_len

    def extract(self, text):
        words = _split(text)
        for length in range(self.start_len, self.stop_len + 1):
            for start, window in enumerate(_windowed(words, length)):
                s = ' '.join(w[1] for w in window)
                for match in self._window_extract(s):
                    yield (window[0][0], len(s), match)

    def _window_extract(self, window):
        '''
        Yield all candidate dicts for a window.

        Must be implemented by subclasses.
        '''
        raise NotImplementedError('Must be implemented by subclasses.')


class PatternExtractor(WindowExtractor):
    '''
    Extractor for regular expression matches.

    Many forms of addresses follow fixed patterns, which can be
    expressed using regular expressions. This class provides an
    extractor for pattern-based location candidates.

    This extractor uses sliding windows of varying sizes, see
    ``WindowExtractor``.
    '''
    def __init__(self, patterns, start_len=2, stop_len=7):
        '''
        Constructor.

        ``patterns`` is a list of *compiled* regular expression objects.
        Each of these must include named groups. The names of the groups
        are used by ``extract`` to build the result dict.

        If you're also using the ``PostalExtractor`` then it is a good
        idea to re-use libpostal's field names for your regular
        expression group names. That way, your validation code will work
        for results from both extractors.

        See ``WindowExtractor`` for the meaning of ``start_len`` and
        ``stop_len``.
        '''
        super(PatternExtractor, self).__init__(start_len, stop_len)
        self.patterns = patterns

    def _window_extract(self, window):
        '''
        Extract potential locations using regular expressions.

        Yields all matches for the patterns (as given to the constructor) in
        ``text``. Each match is reported as a 3-tuple ``(start, length,
        match)``, where ``start`` is the start index of the match in
        ``text``, ``length`` is its length in characters and ``match`` is a
        dict that contains the values of the named groups of the pattern.
        '''
        for pattern in self.patterns:
            m = pattern.search(window)
            if m:
                yield m.groupdict()


class PostalExtractor(WindowExtractor):
    '''
    Extractor for potential locations using *libpostal*.

    libpostal_ is a statistical address parser that supports many
    languages. This extractor passes a text in slices of varying length
    to *libpostal*.

    While this extractor is very versatile it also generates huge
    amounts of false positives -- because there are so many different
    address formats, *libpostal* will recognize a potential address in
    almost anything. Careful validation of the results is therefore
    especially important.

    This extractor uses sliding windows of varying sizes, see
    ``WindowExtractor``.

    .. _libpostal: https://github.com/openvenues/libpostal
    '''
    def __init__(self, start_len=2, stop_len=7):
        '''
        Constructor.

        See the documentation of ``WindowExtractor`` for the meaning
        of ``start_len`` and ``stop_len``.

        Note: The constructor imports the ``postal.parser`` package
        (unless that has happened before), which takes quite some time.
        '''
        super(PostalExtractor, self).__init__(start_len, stop_len)
        import postal.parser  # Lazy import because it takes long
        self._parse_address = postal.parser.parse_address

    def _window_extract(self, window):
        yield dict((key, value) for (value, key)
                   in self._parse_address(window))


class Pipeline(object):
    '''
    A geoextraction pipeline.
    '''
    def __init__(self, locations, extractors=None, validators=None,
                 normalizers=None):
        self.locations = {loc['name'] : loc for loc in locations}
        self.extractors = extractors or []
        self.validators = validators or []
        self.normalizers = normalizers or []
        self._normalize_locations()
        self._setup_components()

    def _setup_components(self):
        for component in itertools.chain(self.extractors, self.validators,
                                         self.normalizers):
            setup = getattr(component, 'setup', None)
            if setup:
                setup(self)

    def _normalize_locations(self):
        '''
        Create a map with normalized location names.
        '''
        self.normalized_names = {}
        for location in self.locations.itervalues():
            self.normalized_names[self._normalize(location['name'])] = location
            for alias in location.get('alias', []):
                self.normalized_names[self._normalize(alias)] = location

    def _augment_result(self, result):
        '''
        Augment a result with information from the location database.
        '''
        # Denormalize names
        for key in ['name', 'street', 'city']:
            try:
                result[key] = self.normalized_names[result[key]]['name']
            except KeyError:
                pass
        # Augment
        try:
            result.update(self.locations[result['name']])
        except KeyError:
            pass

    def extract(self, document):
        candidates = []
        normalized = self._normalize(document)
        for extractor in self.extractors:
            candidates.extend(extractor.extract(normalized))
        for candidate in candidates:
            self._augment_result(candidate[2])
        results = self._prune_overlapping(self._validate(candidates))
        return [result[2] for result in results]

    def _validate(self, candidates):
        '''
        Validate a list of candidate locations.

        Returns a list of all candidates that were approved by all
        validators.
        '''
        validated = []
        for candidate in candidates:
            for validator in self.validators:
                if not validator.validate(candidate[2]):
                    break
            else:
                validated.append(candidate)
        return validated

    def _normalize(self, s):
        '''
        Run a string through all normalizers.
        '''
        for normalizer in self.normalizers:
            s = normalizer.normalize(s)
        return s

    @staticmethod
    def _prune_overlapping(results):
        '''
        Prune overlapping locations.

        If the text region of a location is covered by another result then
        the smaller one is dropped. That way, for each location in the text
        only the longest (and hopefully most complete) variant is kept.
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


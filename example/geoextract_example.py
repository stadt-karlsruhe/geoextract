#!/usr/bin/env python
# encoding: utf-8

'''
Example pipeline for the GeoExtract package.
'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import re

import geoextract
import geoextract.preprocessing


RE_FLAGS = re.UNICODE


#
# STRING NORMALIZATION
#

# Strings must be normalized before searching and matching them. This includes
# technical normalization (e.g. Unicode normalization), linguistic
# normalization (e.g. stemming) and content normalization (e.g. synonym
# handling).

normalizer = geoextract.Normalizer(subs=[(r'str\b', 'strasse')], stem='german')


#
# NAMES
#

# GeoExtract offers multiple extractors that use different techniques for
# extracting locations from text. The easiest one is ``NameExtract``, which
# looks for fixed strings (e.g. the name of POIs).

# These names and their associated data are hard-coded in this example. In
# a real application you would load them from a database. In many cases you
# would also add multiple aliases for the same place.

locations = [
    # POIs
    {
        'name': 'Rathaus',
        'street': 'Karl-Friedrich-Straße',
        'house_number': '10',
        'postcode': '76133',
        'city': 'Karlsruhe',
    },
    {
        'name': 'Konzerthaus',
        'street': 'Festplatz',
        'house_number': '9',
        'postcode': '76133',
        'city': 'Karlsruhe',
    },

    # Streets
    {
        'name': 'Marienstraße',
    },
    {
        'name': 'Karl-Friedrich-Straße',
    },
    {
        'name': 'Rüppurrer Straße',
    },
    {
        'name': 'Karlstraße',
    },
    {
        'name': 'Kaiserstraße',
    },
    {
        'name': 'Festplatz',
    },

    # Cities
    {
        'name': 'Karlsruhe',
    },
]


#
# PATTERNS
#

# For locations that are notated using a semi-structured format (like
# addresses) the ``PatternExtractor`` is a good choice. It looks for
# matches of regular expressions.

# Blocks are named sub-patterns
_BLOCKS = {
    # House number, including potential alphabetical suffix (`12c`)
    # and ranges (`12-23`)
    'house_number': r'([1-9]\d*)[\w-]*',

    # German 5-digit PLZ
    'postcode': r'\d\d\d\d\d',

    # Street name consisting of letters and spaces
    'street': r'[^\W\d_](?:[^\W\d_]| )*[^\W\d_]',

    # City name consisting of letters
    'city': r'[^\W\d_]+',
}

# Patterns can contain blocks via `{block_name}`, these are automatically
# turned into named groups. Patterns are also automatically anchored using
# ^ and $.
_PATTERNS = [
    '{street} {house_number} {postcode} {city}',
    '{street} {house_number}',
]

def _init_pattern_extractor():
    blocks = {key: '(?P<{}>{})'.format(key, value)
               for key, value in _BLOCKS.items()}
    patterns = []
    for pattern in _PATTERNS:
        full = '^' + pattern.format(**blocks) + '$'
        patterns.append(re.compile(full, flags=RE_FLAGS))
    return geoextract.PatternExtractor(patterns)

_pattern_extractor = _init_pattern_extractor()


#
# VALIDATION
#

# Our pattern-based approach will produce a lot of false positives, i.e.
# candidate locations that only look like an address, for example, but do not
# correspond to a real location. These need to be filtered out in a validation
# step by comparing them to reference data (e.g. a list of all valid addresses)
# and/or heuristics.

class Validator(object):

    def setup(self, pipeline):
        self.locations = pipeline.locations

    def validate(self, result):
        if 'name' in result:
            # No need for validation
            return True
        if result['street'] not in self.locations:
            # Discard addresses whose street is not in our list
            return
        m = re.match(r'\d+', result['house_number'])
        num = int(m.group())
        if num > 500:
            # Discard addresses whose house number is larger than 500
            return
        return True


#
# LOCATION EXTRACTION
#

pipeline = geoextract.Pipeline(
    locations,
    extractors=[_pattern_extractor, geoextract.NameExtractor()],
    validators=[Validator()],
    normalizers=[normalizer],
)

# Now it's time to put all pieces together and extract a list of locations from
# a text.

def extract_locations(text):
    '''
    Extract locations from plain text.

    Returns a list of dicts.
    '''
    results = []

    # Split text into whitespace-separated components
    components = geoextract.preprocessing.split_components(text, margin=(1, 2))

    for _, component in components:
        results.extend(pipeline.extract(component))

    return geoextract.unique_dicts(results)


#
# COMMAND LINE INTERFACE
#

if __name__ == '__main__':
    import io
    from pprint import pprint
    import sys

    if len(sys.argv) != 2:
        sys.exit('Usage: {} FILENAME'.format(sys.argv[0]))
    filename = sys.argv[1]

    with io.open(filename, 'r', encoding='utf-8') as f:
        text = f.read()

    locations = extract_locations(text)

    pprint(locations)


#!/usr/bin/env python
# encoding: utf-8

'''
Example pipeline for the GeoExtract package.
'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import re

from nltk.stem.snowball import GermanStemmer
from unidecode import unidecode

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

_stemmer = GermanStemmer()


class Normalizer(object):

    @staticmethod
    def normalize(s):
        '''
        Normalize a string.
        '''
        s = s.strip().lower()

        # Replace Unicode by the closest ASCII-equivalent. Aside from
        # Umlauts and Scharf-S, documents also often contain quotation
        # marks from Microsoft Word and other funny stuff that makes our
        # lives unnecesarily hard.
        s = unidecode(s)

        # Re-join lines broken using a hyphen
        s = re.sub(r'([^\W\d_]-)\s*\n\s*', r'\1', s, flags=RE_FLAGS)

        # Re-join number ranges broken by a newline
        s = re.sub(r'(\d-)\s*\n\s*(?=\d)', r'\1', s, flags=RE_FLAGS)

        # Remove hyphens within words
        s = re.sub(r'([^\W\d_])-+(?=[^\W\d_])', r'\1', s, flags=RE_FLAGS)

        # Replace special characters outside of numbers with spaces. Special
        # characters inside numbers are kept because they help us to
        # distinguish house numbers and post codes from other numbers (e.g.
        # amounts of money). Since we're not looking for particular numbers
        # there's also no problem if they're not normalized.
        s = re.sub(r'(\D|^)\W+(?=\D|$)', r'\1 ', s, flags=RE_FLAGS)
        s = re.sub(r'(\d)\W+(?=\D|$)', r'\1 ', s, flags=RE_FLAGS)
        s = re.sub(r'(\D|^)\W+(\d)', r'\1 \2', s, flags=RE_FLAGS)
        s = re.sub(r'(^|\s+)\W+($|\s+)', ' ', s, flags=RE_FLAGS)

        # Collapse white-space
        s = re.sub(r'\s+', ' ', s, flags=RE_FLAGS)

        # Convert 'str' to 'strasse' at the end of a word
        s = re.sub(r'str\b', 'strasse', s, flags=RE_FLAGS)

        # Stemming. Has pros (e.g. lets us recognize "am Alten Flugplatz" as
        # a match for "Alter Flugplatz") and cons (e.g. "Wir brauchen eine
        # breitere Straße" is now a match for "Breite Straße"). Experiments
        # show that in our case the advantages outweigh the disadvantages.
        s = ' '.join(_stemmer.stem(word) for word in s.split())

        return s


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
        'name': 'Rüppurer Straße',
    },
    {
        'name': 'Karlstraße',
    },
    {
        'name': 'Kaiserstraße',
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
    normalizers=[Normalizer()],
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


#!/usr/bin/env python
# encoding: utf-8

'''
Example pipeline for the GeoExtract package.
'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import re

import geoextract


RE_FLAGS = re.UNICODE


#
# LOCATIONS
#

# GeoExtract uses a database of known locations to geo-reference a document. In
# this example the locations are hard-coded, in a real application they would
# probably be stored in a database.

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

# Many places can be referred to using just their name, for example specific
# buildings (e.g. the Brandenburger Tor), streets (Hauptstraße) or other
# points of interest. These can be extracted using the ``NameExtractor``.
#
# Note that extractor will automatically receive the (normalized) location
# names from the pipeline we construct later, so there's no need to explicitly
# pass them to the constructor.

name_extractor = geoextract.NameExtractor()


#
# PATTERNS
#

# For locations that are notated using a semi-structured format (addresses)
# the ``PatternExtractor`` is a good choice. It looks for matches of regular
# expressions.
#
# The patterns should have named groups, their sub-matches will be
# returned in the extracted locations.

address_pattern = re.compile(r'''
    (?P<street>[^\W\d_](?:[^\W\d_]|\s)*[^\W\d_])
    \s+
    (?P<house_number>([1-9]\d*)[\w-]*)
    (
        \s+
        (
            (?P<postcode>\d{5})
            \s+
        )?
        (?P<city>([^\W\d_]|-)+)
    )?
''', flags=re.UNICODE | re.VERBOSE)

pattern_extractor = geoextract.PatternExtractor([address_pattern])

#
# VALIDATION
#

# The pattern-based approach will produce a lot of false positives, i.e.
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
        try:
            if result['city'] not in self.locations:
                # Discard addresses whose city is not in our list
                return
        except KeyError:
            pass
        return True


#
# PIPELINE CONSTRUCTION
#

# A pipeline connects all the different components.

pipeline = geoextract.Pipeline(
    locations,
    extractors=[pattern_extractor, name_extractor],
    validators=[Validator()],
    normalizers=[normalizer],
)


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

    locations = pipeline.extract(text)

    pprint(sorted(locations))


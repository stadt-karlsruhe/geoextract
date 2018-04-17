#!/usr/bin/env python
# encoding: utf-8

'''
Example pipeline usage for the GeoExtract package.

This example can be used to either extract locations from a file specified on
the command line or (if no additional argument is given) to start a web
server which provides location extraction as a web service.
'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import io
import json
import os
import re

import geoextract


def get_address_pipeline(known_location, substitutions=None, stem='german'):
    '''Returns a pipeline suited for address extraction.'''
    if substitutions is None:
        substitutions = [(r'str\b', 'strasse')]

    #
    # STRING NORMALIZATION
    #

    # Strings must be normalized before searching and matching them. This
    # includes technical normalization (e.g. Unicode normalization),
    # inguistic normalization (e.g. stemming) and content normalization
    # (e.g. synonym handling).

    normalizer = geoextract.BasicNormalizer(substitutions=substitutions,
                                            stem=stem)

    #
    # NAMES
    #

    # Many places can be referred to using just their name, for example
    # pecific buildings (e.g. the Brandenburger Tor), streets (Hauptstraße)
    # or other points of interest. These can be extracted using the
    # ``NameExtractor``.
    #
    # Note that extractor will automatically receive the (normalized)
    # location names from the pipeline we construct later, so there's
    # no need to explicitly pass them to the constructor.

    name_extractor = geoextract.NameExtractor()

    #
    # PATTERNS
    #

    # For locations that are notated using a semi-structured format
    # (addresses) the ``PatternExtractor`` is a good choice. It looks
    # for matches of regular expressions.
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
    # POSTPROCESSING
    #

    # Once locations are extracted you might want to postprocess them, for
    # example to remove certain attributes that are useful for validation
    # but are not intended for publication. Or you may want to remove a
    # certain address that's printed in the footer of all the documents
    # you're processing. GeoExtract allows you to do this by using one or
    # more postprocessors. In this example we will remove all but a few
    # keys from our location dicts.

    keys_to_keep = ['name', 'street', 'house_number', 'postcode', 'city']
    key_filter_postprocessor = geoextract.KeyFilterPostprocessor(keys_to_keep)

    #
    # PIPELINE CONSTRUCTION
    #

    # A pipeline connects all the different components.
    #
    # Here we're using custom extractors and a custom normalizer. We could
    # also provide our own code for splitting a document into chunks and
    # for validation, but for simplicity we'll use the default implementations
    # in these cases.

    return geoextract.Pipeline(
        known_location,
        extractors=[pattern_extractor, name_extractor],
        normalizer=normalizer,
        postprocessors=[key_filter_postprocessor],
    )


def main():
    '''Runs the example with the cli arguments.'''
    file = os.path.realpath(__file__)
    default_path = os.path.join(os.path.dirname(file), 'locations.json')

    parser = argparse.ArgumentParser()
    parser.add_argument('filename', nargs='?', default=None)
    parser.add_argument('--locations', default=default_path)
    args = parser.parse_args()

    # GeoExtract requries a list of known locations to geo-reference
    # document.
    #
    # The ``type`` attribute is used for validation, for example to ensure that
    # the string matched for an address' street is actually a street.

    with open(args.locations) as fp:
        locations = json.load(fp)

    pipeline = get_address_pipeline(locations)

    if not args.filename:
        # Serve web API
        pipeline.create_app().run()
    else:
        # Extract locations from the given file
        with io.open(args.filename, 'r', encoding='utf-8') as f:
            text = f.read()
        locations = pipeline.extract(text)
        print(json.dumps(locations, indent=4, sort_keys=True))


if __name__ == '__main__':
    main()

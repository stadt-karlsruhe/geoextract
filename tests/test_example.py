#!/usr/bin/env python
# encoding: utf-8

# Copyright (c) 2016-2017, Stadt Karlsruhe (www.karlsruhe.de)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

'''
Tests for the example provided with the geoextract package.
'''


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import io
import json
import os.path
import subprocess
import sys

import requests

from . import sort_as_json, stop_process, wait_for_server


EXAMPLE_DIR = os.path.join(os.path.dirname(__file__), '..', 'example')
EXAMPLE_SCRIPT = os.path.join(EXAMPLE_DIR, 'geoextract_example.py')
EXAMPLE_INPUT = os.path.join(EXAMPLE_DIR, 'sample_input.txt')
EXAMPLE_PORT = 5000
EXAMPLE_URL = 'http://localhost:{}'.format(EXAMPLE_PORT)

EXAMPLE_DATA = [
    {
        'name': 'Rüppurrer Straße'
    },
    {
        'house_number': '1000',
        'street': 'Festplatz'
    },
    {
        'house_number': '11c',
        'street': 'Festplatz'
    },
    {
        'house_number': '3',
        'street': 'Kaiserstraße'
    },
    {
        'house_number': '3-19',
        'street': 'Festplatz'
    },
    {
        'house_number': '943',
        'street': 'Karl-Friedrich-Straße'
    },
    {
        'city': 'Karlsruhe',
        'house_number': '12',
        'postcode': '76137',
        'street': 'Rüppurrer Straße'
    },
    {
        'city': 'Karlsruhe',
        'house_number': '7',
        'postcode': '76133',
        'street': 'Karlstraße'
    },
    {
        'city': 'Karlsruhe',
        'house_number': '8',
        'postcode': '76133',
        'street': 'Kaiserstraße'
    },
    {
        'city': 'Karlsruhe',
        'house_number': '10',
        'name': 'Rathaus am Marktplatz',
        'postcode': '76133',
        'street': 'Karl-Friedrich-Straße'
    },
    {
        'city': 'Karlsruhe',
        'house_number': '9',
        'name': 'Konzerthaus',
        'postcode': '76133',
        'street': 'Festplatz'
    }
]


def test_example_with_file():
    '''
    Test that running the example with input from a file works.
    '''
    output = subprocess.check_output(['python', EXAMPLE_SCRIPT, EXAMPLE_INPUT])
    if isinstance(output, bytes):
        output = output.decode(sys.stdout.encoding)
    data = json.loads(output)
    assert sort_as_json(data) == sort_as_json(EXAMPLE_DATA)


def make_extract_api_request(url, text):
    '''
    Extract locations from a text using the web API.
    '''
    url = url.rstrip('/') + '/api/v1/extract'
    r = requests.post(url, files={'text': ('input.txt', text)})
    r.raise_for_status()
    return r.json()


def test_example_as_app():
    '''
    Test that running the example as an app works.
    '''
    process = subprocess.Popen(['python', EXAMPLE_SCRIPT])
    try:
        wait_for_server(EXAMPLE_URL)
        with io.open(EXAMPLE_INPUT, encoding='utf-8') as f:
            text = f.read()
        extracted = make_extract_api_request(EXAMPLE_URL, text)
        assert sort_as_json(extracted) == sort_as_json(EXAMPLE_DATA)
    finally:
        stop_process(process.pid, delay=10)

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
Tests for the geoextract web app.
'''


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import contextlib
import multiprocessing

from bs4 import BeautifulSoup
import requests

from geoextract import __version__ as geoextract_version, Pipeline
from . import stop_process, wait_for_server


SERVER_URL = 'http://localhost:5000'
EXTRACT_URL = SERVER_URL + '/api/v1/extract'


class AppProcess(multiprocessing.Process):
    '''
    Process for running and stopping an app server.
    '''

    def __init__(self, *args, **kwargs):
        '''
        Set up a new geoextract app.

        All arguments are passed to ``geoextract.Pipeline``.
        '''
        super(AppProcess, self).__init__()
        self.pipeline = Pipeline(*args, **kwargs)
        self.app = self.pipeline.create_app()

    def run(self):
        '''
        Start the app in a separate process.
        '''
        self.app.run()

    def stop(self):
        '''
        Stop the app.
        '''
        if self.pid is None:
            raise RuntimeError('Process is not running.')
        stop_process(self.pid, delay=10)


@contextlib.contextmanager
def app(locations=(), *args, **kwargs):
    '''
    Context manager that provides a geoextract app.

    All arguments are passed on to ``geoextract.Pipeline``.
    '''
    process = AppProcess(locations, *args, **kwargs)
    process.start()
    try:
        wait_for_server(SERVER_URL)
        yield
    finally:
        process.stop()


def html2text(html):
    '''
    Extract the text of a piece of HTML code.
    '''
    return BeautifulSoup(html, 'html.parser').get_text()


class TestApp(object):
    '''
    Tests for the web app.
    '''

    def test_extract_get(self):
        '''
        Test that GET requests to ``extract`` fail.
        '''
        with app():
            r = requests.get(EXTRACT_URL)
            assert r.status_code == 405

    def test_extract_no_input(self):
        '''
        Test calling ``extract`` with no input.
        '''
        with app():
            r = requests.post(EXTRACT_URL)
            assert r.status_code == 400
            assert 'Missing "text" parameter' in html2text(r.text)

    def test_extract_no_utf8(self):
        '''
        Test calling ``extract`` with text that isn't UTF-8.
        '''
        with app():
            not_utf8 = 'öäü'.encode('latin1')
            r = requests.post(EXTRACT_URL, files={'text': ('x.txt', not_utf8)})
            assert r.status_code == 400
            text = html2text(r.text)
            assert 'Decoding error' in text
            assert 'UTF-8' in text

    def test_extract_success(self):
        '''
        Test a successful call of ``extract``.
        '''
        locations = [{'name': 'a-location'}]
        with app(locations):
            text = 'a-location is the place to be'
            r = requests.post(EXTRACT_URL, files={'text': ('x.txt', text)})
            assert r.status_code == 200
            assert r.json() == locations

    def test_root(self):
        '''
        Test accessing the root document.
        '''
        with app():
            r = requests.get(SERVER_URL)
            text = html2text(r.text)
            assert 'GeoExtract' in text
            assert geoextract_version in text

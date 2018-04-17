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
Web app providing an GeoExtract web API.
'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from flask import abort, Flask, jsonify, request


def create_app(pipeline):
    '''
    Create a Flask app for serving a pipeline as a web service.

    ``pipeline`` is an instance of ``geoextract.Pipeline``.

    Returns a Flask app that exposes the pipeline's ``extract`` method
    as a web API endpoint at ``/api/v1/extract``. The end point takes
    a single file-upload POST parameter named ``text`` which contains
    the UTF-8 encoded raw text from which locations should be extracted.
    '''
    app = Flask('geoextract')
    app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1 MB

    # Late import to avoid circular dependency
    import geoextract

    @app.route('/')
    def index():
        return 'GeoExtract {}'.format(geoextract.__version__)

    @app.route('/api/v1/extract', methods=['POST'])
    def extract():
        try:
            text = request.files['text'].read().decode('utf-8')
        except KeyError:
            abort(400, 'Missing "text" parameter.')
        except UnicodeDecodeError:
            abort(400, 'Decoding error. Data must be encoded as UTF-8.')
        return jsonify(pipeline.extract(text))

    return app

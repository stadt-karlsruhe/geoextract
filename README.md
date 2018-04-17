# GeoExtract

[![Travis CI badge](https://travis-ci.org/stadt-karlsruhe/geoextract.svg?branch=master)](https://travis-ci.org/stadt-karlsruhe/geoextract) [![Coveralls badge](https://coveralls.io/repos/github/stadt-karlsruhe/geoextract/badge.svg)](https://coveralls.io/github/stadt-karlsruhe/geoextract)

GeoExtract is a web service and Python package for extracting locations
(addresses, street names, points of interest) from free-form text.


## Background

Extracting locations and addresses from free-form text is a difficult task,
since addresses can take [many different forms][falsehoods]. Hence, in an
international context, almost any combination of words and numbers may
represent an address. Even if the target region is more constrained
geographically there are often parts of a text which look like genuine
references to locations but which do not describe an actually existing place.

Therefore, some way of validating potential locations is required. How that
is achieved depends heavily on the use case and the available data. For example
you might have a database with all valid addresses (e.g. from
[OpenAddresses][openaddresses]), in which case you can perform a very detailed
validation. In other cases, you might only have a list of valid street names
and will have to validate house numbers heuristically.

GeoExtract helps you to find potential locations and to filter and organize
validated candidates. It is no turnkey solution but instead provides a
framework on which you can build a solution for your use case.

[falsehoods]: https://www.mjt.me.uk/posts/falsehoods-programmers-believe-about-addresses/
[openaddresses]: https://openaddresses.io/


## Installation

GeoExtract runs on Python 2.7 and 3.4 or later.

GeoExtract relies on [NumPy][numpy] and [SciPy][scipy], which are cumbersome
to install from source. We therefore suggest to use your system's package
manager to install them via pre-built packages. For example, on Ubuntu you
would use

    sudo apt-get install python-numpy python-scipy

We also recommend to use a [virtualenv][virtualenv] for installing
GeoExtract. Make sure to pass the `--system-site-packages` parameter so that
the virtualenv picks up the system-wide installations of NumPy and SciPy:

    virtualenv -p python2 --system-site-packages my_virtualenv
    source my_virtualenv/bin/activate

Installing GeoExtract is then easy using [pip][pip]:

    pip install git+https://github.com/stadt-karlsruhe/geoextract.git

[numpy]: http://www.numpy.org/
[scipy]: https://www.scipy.org/
[virtualenv]: https://virtualenv.pypa.io
[pip]: https://pip.pypa.io


## Usage

GeoExtract provides a pipeline for organizing the extraction process of
preparing the input text, and for extracting, validating and consolidating
locations from it. The default implementations for each step can be configured
or replaced by your own variants.

See the `example` directory for a detailed example of using GeoExtract. The
script takes a text file and extracts the locations. Due to the built-in
validation this only works for locations that the script knows about, therefore
a sample input file is also included:

    python example/geoextract_example.py example/sample_input.txt

If no parameter is given then the example script starts a web server which
provides location extraction as a web service:

    python example/geoextract_example.py

To use the web service, send a POST request to `/api/v1/extract`. The request
must have a parameter `text` containing the UTF-8 encoded text. For example,
using the excellent [HTTPie] client:

    http -f post http://localhost:5000/api/v1/extract text@example/sample_input.txt

[HTTPie]: https://httpie.org/


## Deployment

To deploy GeoExtract as a web service, construct an instance of
`geoextract.Pipeline` (see the example in the `example` directory) and turn it
into a [Flask] app via the `create_app` method. You can then deploy that app
using the usual approaches for [deploying Flask applications].

[Flask]: http://flask.pocoo.org
[deploying Flask applications]: http://flask.pocoo.org/docs/latest/deploying/


## Development

First clone the repository:

    git clone https://github.com/stadt-karlsruhe/geoextract.git
    cd geoextract

Install the development requirements (ideally inside a [virtualenv]):

    pip install -r dev-requirements.txt

To run the tests:

    tox

To run the linter:

    flake8


## History

See `CHANGELOG.md`.


## License

Copyright (c) 2016-2018, Stadt Karlsruhe (www.karlsruhe.de)

Distributed under the MIT license, see the file `LICENSE` for details.


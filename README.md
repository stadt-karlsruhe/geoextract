# GeoExtract

This library provides a framework for extracting locations (addresses,
street names, points of interest) from free-form text. It is intended
for geo-referencing existing documents.


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
validated candidates. It is by no means a turnkey solution but instead provides
a framework on which you can build a solution for your use case.

[falsehoods]: https://www.mjt.me.uk/posts/falsehoods-programmers-believe-about-addresses/
[openaddresses]: https://openaddresses.io/


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


## Installation

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


## Development

First clone the repository:

    git clone https://github.com/stadt-karlsruhe/geoextract.git
    cd geoextract

Make sure you have [NumPy][numpy] and [SciPy][scipy] installed. For example,
on Ubuntu:

    sudo apt-get install python-numpy python-scipy

Create a virtualenv:

    virtualenv -p python2 --system-site-packages venv
    source venv/bin/activate

Install GeoExtract in development mode:

    python setup.py develop


## License

Copyright (c) 2016, Stadt Karlsruhe (www.karlsruhe.de)

Distributed under the MIT license, see the file `LICENSE` for details.


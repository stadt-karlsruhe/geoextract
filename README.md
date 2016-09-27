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

Therefore, some way of validating potential addresses is required. How that
is achieved depends heavily on the use case and the available data. For example
you might have a database with all valid addresses (e.g. from
[OpenAddresses][openaddresses]), in which case you can perform a very detailed
validation. In other cases, you might only have a list of valid street names
and will have to validate house numbers heuristically.

GeoExtract helps you to find potential addresses and to filter and organize
validated candidates. It is by no means a turnkey solution but instead provides
a framework on which you can build a solution for your use case.

[falsehoods]: https://www.mjt.me.uk/posts/falsehoods-programmers-believe-about-addresses/
[openaddresses]: https://openaddresses.io/


## Usage

The general workflow when using GeoExtract to extract locations from a document
looks like this:

1. *You:* **Extract plain text from the document.** Although this is often easy
   it is nevertheless important to get right: the different approaches of text
   extraction often differ in their treatment of whitespace, tabular content,
   etc., and the right tool and options can make the following steps much
   easier.

2. *You:* **Prepare the plain text.** This step can be as simple as converting
   everything to lowercase but it can also involve more complicated
   pre-processing like Unicode normalization, whitespace regularization and
   stemming. The precise requirements will again depend on your use case.

3. *GeoExtract:* **Find candidate locations.** There are multiple extractors to
   help you with this, which can look for fixed strings (e.g. the name of POIs),
   regular expression matches or things that heuristically look like an address.

4. *You:* **Validate the candidates.** Sort out anything that's not a real
   location (whatever that means in your context).

5. *GeoExtract:* **Consolidate the validated locations.** This is a post-
   processing step that selects the most complete location from multiple
   variants extracted from the same location. For example, for an address
   containing a street name and a house number there might be two valid
   candidates, one containing just the street name and the other containing
   both the name and the number, and the former will be removed during post-
   processing. In addition, duplicate locations from different parts of the
   same document are removed.


## API

The main classes of *GeoExtract* are the subclasses of `Extractor`, which
implement different strategies for finding candidate locations:

- `NameExtractor` efficiently looks for fixed strings in the text. Useful for
  finding names, for example of streets, districts or points of interest.

- `PatternExtractor` looks for matches of user-specified regular expressions.
  Useful for finding addresses in known formats.

- `PostalExtractor` uses [libpostal][libpostal] to extract location candidates
  heuristically. It produces loads of false positives (which you need to prune
  during validation) but supports a wide range of address formats. Requires
  [pypostal][pypostal] to be installed.

Typically you will combine multiple extractors. Their `extract` method yields
candidate locations, which you need to validate. Once you have a set of
validated locations you can use `geoextract.reduce_locations` to prune
incomplete and overlapping variants of the same location. Finally, use
`geoextract.unique_dicts` to remove duplicate discoveries of the same location
in a single document.

[libpostal]: https://github.com/openvenues/libpostal
[pypostal]: https://github.com/openvenues/pypostal


## License

Copyright (c) 2016, Stadt Karlsruhe (www.karlsruhe.de)

Distributed under the MIT license, see the file `LICENSE` for details.


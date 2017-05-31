# Change Log for GeoExtract

The format of this file is based on [Keep a Changelog], and this
project uses [Semantic Versioning].


## [0.2.0] (2017-05-31)

### Added

- Simple web app for providing geo extraction as a web service.

- `geoextract.NameValidator` is a simple validator that ensures that the
  named locations referred to by an extracted location (for example a street
  street name) actually exist in the location database.

- `geoextract.Normalizer` is a versatile string normalizer.

- `geoextract.KeyFilterPostProcessor` is a simple postprocessor that only keeps

### Changed

- GeoExtract now uses a pipeline architecture that covers all aspects of the
  location extraction process.

- `geoextract.NameExtractor` doesn't take the target names as a constructor
  argument anymore, instead they are automatically provided by the pipeline.

- The module `geoextract.preprocessing` was renamed to `geoextract.splitters`,
  and the `geoextract.preprocessing.split_components` function has been
  refactored into the `geoextract.splitters.WhitespaceSplitter` class.

### Removed

- `geoextract.reduce_locations` and `geoextract.unique_dicts` were merged into
  the pipeline architecture and aren't available as a standalone functions
  anymore.


## [0.1.0] (2017-05-02)

First release.


[Keep a Changelog]: http://keepachangelog.com
[Semantic Versioning]: http://semver.org/

[0.2.0]: https://github.com/stadt-karlsruhe/geoextract/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/stadt-karlsruhe/geoextract/commits/v0.1.0


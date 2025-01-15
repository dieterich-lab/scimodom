# Change Log

All notable changes to scimodom will be documented in this file.
The format is based on [Keep a Changelog](http://keepachangelog.com/), and this project adheres to [Semantic Versioning](http://semver.org/).

## [Release candidate] - started 2025-01

## [3.1.1] - 2025-01-15

### Fixed

- ValidationError for IntersectResponse in `/api/v0/modification/target/RBP?` (Bed6Record DTO).
- EUFID link in ModificationSiteTable.

### Changed

- dev and tests dependencies
- node/npm version

## [3.1.0] - 2025-01-08

### Added

- bedRMod validation in Comparison (#92)
- TypeScript

### Changed

- API version management
- utils
- Error handling
- Documentation

### Fixed

- URL constructor
- Gene cache management
- EUF toggle in Comparison
- SMID/EUFID length validation

## [3.0.0] 2024-09-25

### Added

- Search table full export (#151)
- Search query modalities (gene search)
- Link to Ensembl gene table (#140)
- Chart data caching, CLI-related utilities, and update on import

### Changed

- Search API
- Minor changes to the web interface (info button)
- Link to matched Ensembl version (110)

### Fixed

- Missing query for chromosome end
- Annotation: missing records (#141)
- Annotation: feature, gene, and biotype association (#139)

## [2.0.6] 2024-08-15

First release.

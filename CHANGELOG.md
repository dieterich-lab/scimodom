# Change Log
All notable changes to webdorina will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/), 
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased] - started 2023

Migration

## [Unreleased] - started 2020-07-20

### Updated
- redis and rq, Python 3.9 (remove all pins)

### Changed
- config for our current setup

### Added

### Fixed
- Temporarily pin versions of redis and rq (redis-py 3.0 has backwards incompatible changes that breaks webdorina).
- Remove pins, fix SETEX args order, fix SET bool 

### Removed
- Temporarily ignore get_tissues in `app.py`, modified `dorina.js`, `search.html` (TODO)

## [0.5] 2020-07-20

Prior to this date, changes to this project were not documented.

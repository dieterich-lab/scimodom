Change log
^^^^^^^^^^

All notable changes to scimodom will be documented in this file.
The format is based on `Keep a Changelog <http://keepachangelog.com>`_, and this project adheres to `Semantic Versioning <http://semver.org>`_.

[Unreleased] - 2025-05
""""""""""""""""""""""

**Fixed**

- Liftover of thick coordinates :issue:`122`
- Add unique constraint to data records
- OverflowError :issue:`180`

**Changed**

- Update to euf-specs v2 :issue:`167`, :issue:`175`
- Database migration :issue:`167`
- Display of missing coverage and frequency for BED6

**Added**

- Validation of thick coordinates for import (not in DTOs or ORM models)

**Removed**

- Offending datasets (Nm-Mut-seq, m7G-seq)

[4.0.2] - 2025-04-30
""""""""""""""""""""

**Fixed**

- Form (date validation) :issue:`162`
- Database schema/migration and :issue:`166`
- CLI (project delete) :issue:`178`
- Vitest vulnerability

**Changed**

- Documentation

**Added**

- Favicon

**Removed**

- RBP logos-related code

[4.0.1] - 2025-03-26
""""""""""""""""""""

**Fixed**

- :issue:`165`

[4.0.0] - 2025-03-10
""""""""""""""""""""

**Fixed**

- Gene cache query missing filter for modification.

**Changed**

- CLI
- Documentation

**Added**

- CLI tests

[3.1.1] - 2025-01-15
""""""""""""""""""""

**Fixed**

- ValidationError for IntersectResponse in ``/api/v0/modification/target/RBP?`` (Bed6Record DTO).
- EUFID link in ModificationSiteTable.

**Changed**

- dev and tests dependencies
- node/npm version

[3.1.0] - 2025-01-08
""""""""""""""""""""

**Fixed**

- URL constructor
- Gene cache management
- EUF toggle in Comparison
- SMID/EUFID length validation

**Changed**

- API version management
- utils
- Error handling
- Documentation

**Added**

- bedRMod validation in Comparison (:issue:`92`)
- TypeScript

[3.0.0] 2024-09-25
""""""""""""""""""

**Fixed**

- Missing query for chromosome end
- Annotation: missing records (:issue:`141`)
- Annotation: feature, gene, and biotype association (:issue:`139`)

**Changed**

- Search API
- Minor changes to the web interface (info button)
- Link to matched Ensembl version (110)

**Added**

- Search table full export (:issue:`151`)
- Search query modalities (gene search)
- Link to Ensembl gene table (:issue:`140`)
- Chart data caching, CLI-related utilities, and update on import

[2.0.6] 2024-08-15
""""""""""""""""""

First release.

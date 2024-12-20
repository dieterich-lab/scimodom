# Sci-ModoM

Sci-ModoM is a quantitative database of RNA modifications dedicated to novel assays that provide transcriptome-wide information at
single-base resolution.

<p align="center">
  <a href="https://dieterich-lab.github.io/scimodom/index.html"><img alt="Sci-ModoM" src="https://github.com/dieterich-lab/scimodom/raw/master/server/docs/source/_static/logo.png"></a>
</p>

<p align="center">
<a href="https://dieterich-lab.github.io/scimodom/index.html"><img alt="docs" src="https://github.com/dieterich-lab/scimodom/actions/workflows/static.yml/badge.svg"></a>
<a href="https://doi.org/10.5281/zenodo.13911907"><img alt="DOI" src="https://zenodo.org/badge/DOI/10.5281/zenodo.13911907.svg"></a>
<a href="https://img.shields.io/github/v/release/dieterich-lab/scimodom"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/dieterich-lab/scimodom"></a>
<a href="https://www.gnu.org/licenses/agpl-3.0"><img alt="License: AGPL v3" src="https://img.shields.io/badge/License-AGPL_v3-blue.svg"></a>
</p>

---

## Documentation

The application consists of the following components:

- Database: MariaDB (migrations handled using Alembic)
- Server: A REST-API backend using the SQLAlchemy Database Toolkit for Python and Flask
- Client: A Web-GUI using Vue.js and the PrimeVue Tailwind CSS based UI component library

Consult the [Documentation](https://dieterich-lab.github.io/scimodom/index.html) for installation instructions, containers orchestration, general information about the data model or how to use the CLI, and for the latest bedRMod specifications.

General documentation is also available online at [Sci-ModoM - Documentation](https://scimodom.dieterichlab.org/documentation/about).

## How to report issues

For bugs, issues, or feature requests, use the [bug tracker](https://github.com/dieterich-lab/scimodom/issues). Follow the instructions and guidelines given in the templates.

## How to cite

Etienne Boileau, Harald Wilhelmi, Anne Busch, Andrea Cappannini, Andreas Hildebrand, Janusz M. Bujnicki, Christoph Dieterich. [Sci-ModoM: a quantitative database of transcriptome-wide high-throughput RNA modification sites](https://academic.oup.com/nar/advance-article/doi/10.1093/nar/gkae972/7875981), _Nucleic Acids Research_, 2024;, gkae972, [https://doi.org/10.1093/nar/gkae972](https://doi.org/10.1093/nar/gkae972).

## License

GNU Affero General Public Licence (AGPL) version 3.

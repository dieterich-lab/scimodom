#!/usr/bin/env python
# -*- coding: utf-8
"""
Created on 09:32 10/10/2017 2017

"""
from __future__ import unicode_literals
import os
from os import path
import logging
from ftplib import FTP, all_errors

import requests
from six.moves.urllib.request import urlretrieve, urlopen
from six.moves.urllib.error import URLError

from scimodom.dorina.utils import check_file_extension, uncompress
from scimodom.dorina.config import config

log = logging.getLogger(__name__)


class EnsemblFTP(object):
    """
    Base template for retrieving file and information from Ensembl FTP server.

    .. important:: Despite some of the function document on directory
    hierarchy there is no warranty that the structure will work for all
    organisms. In fact, it won't.
    """

    def __init__(self, release=config.get('DEFAULT', 'version'),
                 organism=config.get('DEFAULT', 'organism')):
        self.base_url = 'ftp.ensemblorg.ebi.ac.uk'
        self.url = []
        self.local_data = config.get('DEFAULT', 'data_path')
        self.release = release
        self.organism = organism
        self.available = {}
        self._file_name = None

        try:
            self.assembly = self.get_assembly(
                version=release, organism=self.organism)
        except URLError:
            raise ValueError(
                'Unable to retrieve assembly information for {}  release {}, '
                'probably because unsupported release number (last supported '
                'release number for homo_sapiens is 67.')

        try:
            os.makedirs(
                path.join(self.local_data + self.assembly + '_' + self.release))
        except OSError:
            log.info('{} exists, aborting makedir.'.format(
                path.join(self.local_data + self.assembly)))
            pass  # dir exists

    def check_available(self, url):
        """
        List the files and directories available at the FTP server.

        :param str url: location to be listed
        """
        if not url.startswith('/'):
            url = '/' + url
        available_dir = None
        ftp = FTP(self.base_url)
        try:
            ftp.login()
            available_dir = ftp.nlst(url)
        except all_errors as e:
            log.error('FTP error.')
            raise e
        finally:
            ftp.close()

        if not available_dir:
            log.warning('No available files in {}'.format(self.base_url + url))

        self.available[url] = available_dir

    def check_local(self, basename):
        """Check if file has been downloaded before."""
        if '/' in basename:
            raise NameError('This {} seems a filename, not a basename.'.format(
                basename))

        return path.isfile(path.join(self.local_data, self.assembly, basename))

    def filename_from_url(self, url):
        remote_path, filename = url.rsplit('/', 1)
        return path.join(self.local_data, self.assembly, filename)

    def retrieve_file_from_url(self, url, force=False):
        """
        Retrieve a file from FTP server.
        .. note:: urlretrieve has a better API for error handling than
        ftp.retrbinary

        :param bool force: overwrite local files
        :param str url: file url
        :return bool: whether retrieved
        """
        remote_path, basename = url.rsplit('/', 1)

        filename = path.join(self.local_data, self.assembly, basename)
        if not force and self.check_local(basename.replace('.gz', '')):
            log.info('{} available, aborting retrieval.'.format(filename))
            return False
        else:
            try:
                urlretrieve('ftp://' + self.base_url + url, filename)
                log.info('{} retrieval complete.'.format(filename))
                return True
            except URLError as e:
                log.error('Error retrieving {}: \n{}'.format(
                    'ftp://' + self.base_url + url, e))
                raise e

    def retrieve_all(self):
        for url in reversed(self.url):
            try:
                retrieved = self.retrieve_file_from_url(url)
            except (IOError, ) as e:
                self.url = []
                raise e

            filename = self.filename_from_url(url)
            if retrieved:
                uncompress(filename)
            self.url.remove(url)
            yield filename

    def check_extension(self, extension):
        """
        Check for error in the built urls
        :param str extension: file extension
        :raise ValueError: if the file extension is not in url
        """

        self.url = [url for url in self.url
                    if check_file_extension(url, extension)]

    def list_ftp_directory(self, directory):
        """
        .. notes:: substitutes check_available

        :param str directory:
        :return list: listed files on the FTP directory
        """
        response = urlopen('ftp://' + self.base_url + directory)
        txt = response.read()
        return [str(x).split()[-1] for x in txt.splitlines()]

    def get_assembly(self, version=None, organism=None):
        """
        This is a hack to get the Assembly for a Ensembl release and organism.
        For currently release, just use the REST .
        :param str version: release version
        :param str organism: organism name
        :return str: assembly name
        """
        if version is None:
            version = self.release
        if organism is None:
            organism = self.organism
        url = u'/pub/{}/data_files/{}/'.format(version, organism)
        directory_list = self.list_ftp_directory(url)

        return directory_list[0].replace("'", "")

    def retrieve_from_tsv_by_index(self, extension='tsv.gz', file_index=5):
        """
        Retrieves files from the TSV directory from Ensembl TSV.
        -  CHECKSUM
        -  Compara ncrna homologies
        -  Compara protein homologies
        -  Ena mappings
        -  Entrez mappings
        -  Karyotype (similar to UCSC genome files)
        -  refseq mappings
        -  Uniprot Uniprot
        -  README Ena
        -  README Entrez
        -  README refseq
        -  README Uniprot

        Default is the karyotype file with chromosome's lengths
        """
        url = u'/pub/{}/tsv/{}/'.format(self.release, self.organism)
        self.check_available(url)
        self.url.append(self.available[url][file_index])
        self.check_extension(extension)

        return list(self.retrieve_all())

    def retrieve_from_gff_by_index(self, extension='gff3', file_index=-2):
        """
        Retrieves GFF3 files from Ensembl FTP server.
        For the gff3 directory structure is:
        - CHECKSUMS
        - abinitio file
        - chromosome file
        - a file for each chromosome
        - a complete file with every chromosome
        - README

        Default is the GFF3 file with all chromosomes
        """
        url = u'/pub/{}/{}/{}/'.format(self.release, extension, self.organism)
        self.check_available(url)
        self.url.append(self.available[url][file_index])
        self.check_extension(extension)

        return list(self.retrieve_all())

    def retrieve_full_gff(self):
        """
        Retrieves the GFF3 file that contains all chromossomes from Ensembl FTP
        server.
        .. note::
        /pub/release-90/gff3/homo_sapiens/Homo_sapiens.GRCh38.90.gff3.gz
        """

        url = u'/pub/{}/gff3/{}/{}.{}.{}.gff3.gz'.format(
            self.release, self.organism, self.organism.capitalize(),
            self.assembly, self.release[-2:])
        self.url.append(url)
        return list(self.retrieve_all())

    def retrieve_full_vcf(self, extension='vcf.gz'):
        """
        Retrieves Regulation VCS files from Ensembl Variation FTP server.
        The regulation directory structure is:
        -  CHECKSUM
        -  Peaks
        -  QualityCheck
        -  RegulatoryFeatureActivity
        -  Regulatory features
        -  Motif features

        .. note:
        Only available for human and mice.
        """
        # /pub/release-90/variation/vcf/homo_sapiens/Homo_sapiens.vcf.gz
        self.url.append(u'/pub/{}/variation/vcf/{}/{}.{}'.format(
            self.release, self.organism, self.organism.capitalize(), extension))
        self.check_extension(extension)

        return list(self.retrieve_all())

    def retrieve_from_regulation_by_experiment(self, extension='bed',
                                               tissue=None, experiment='*'):
        """
        Retrieves Regulation bed files from Ensembl FTP server by experiment
        name. For Human, the regulation directory structure is:
        -  CHECKSUM
        -  Peaks
        -  QualityCheck
        -  RegulatoryFeatureActivity
        -  Regulatory features
        -  Motif features

        .. note:
        Only available for human and mice.
        """
        if tissue is None:
            tissue = config.get('DEFAULT', 'tissue')
        url = u'/pub/{}/regulation/{}/Peaks/{}/{}'.format(self.release,
                                                          self.organism,
                                                          tissue,
                                                          experiment)

        if '*' in url:
            url = url.replace('*', '')

        self.check_available(url)
        for _url in self.available[url]:
            self.check_available(_url)
        del self.available[url]
        [self.url.extend(x) for x in list(self.available.values())]
        self.check_extension(extension)

        return list(self.retrieve_all())


class EnsemblRest(object):
    """
    Base class for retrieving data from Ensembl Rest API.

    Limited support to previous Ensembl release using:
    >>> rest = EnsemblRest(base_url='grch37.rest.ensembl.org')
    >>> rest.ping()
    """

    def __init__(self, **kwargs):
        self.base_url = kwargs.get('base_url', 'http://rest.ensembl.org/')
        self.headers = kwargs.get('headers',
                                  {'content-type': 'application/json'})
        self.reqs_per_sec = 15
        self.session = requests.Session()

    def ping(self):
        ext = "info/ping?"

        return self.get(ext)

    def get_info_assembly(self, organism):
        ext = 'info/assembly/{}/X?'.format(organism)
        return self.get(ext)

    def get_genetree_members_by_id(self, ensembl_id, params=None):
        """
        Retrieves genetree for a given Ensembl stable id.

        :param str ensembl_id: Ensembl stable id
        :param dict params:

        :return dict: genetree result

        ..note::
        This endpoint supports isoform identification for protein ids, such as
        ENSP00000288602.6, but not for transcripts, as ENST00000288602.10

        """
        # params = {'aligned': 0, 'callback': '-', 'cigar_line': 0,
        # 'clusterset_id': '-', 'db_type': '-', 'nh_format': 'simple',
        # 'object_type': [], 'prune_species': '-', 'prune_taxon': '-',
        # 'sequence': 'protein', 'species': '-'}
        if '.' in ensembl_id:
            ensembl_id = ensembl_id.split('.')[0]
            log.info('Isoform identifier detected, falling back to stable ID '
                     '{}'.format(ensembl_id))
        ext = 'genetree/member/id/{}?'.format(ensembl_id)
        return self.get(ext, params=params)

    def get_genomic_alignment(self):
        pass

    def get_phenotype_by_region(self, organism, chromosome, start, end):
        """
        ..Note Maximum region length is 5 Mb.
        :param str organism: Organism scientific name, such as homo_sapiens
        :param int chromosome: Chromosome number, eg: 9
        :param int start: First base pair of the query in genomic region
        (0 based index)
        :param int end: Last base of the query in the genomic region (inclusive)
        :return dict:
        """
        ext = "/{}/{}:{}-{}?".format(organism, chromosome, start, end)
        return self.get(ext)

    def get(self, ext, json=True, headers=None, params=None):
        """

        :param ext:
        :param json:
        :param headers:
        :param params:
        :return:
        """
        if headers is None:
            headers = self.headers
        r = requests.get(self.base_url + ext, headers=headers, params=params)
        if not r.ok:
            r.raise_for_status()

        if json:
            return r.json()
        else:
            return r.content

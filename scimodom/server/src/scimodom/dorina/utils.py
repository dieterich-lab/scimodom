#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import unicode_literals
import gzip
import logging
import os
import json
import shutil
from os import path
from io import open

log = logging.getLogger(__name__)

assembly_mapping = {
    'hg38': 'h_sapiens',
    'mm10': 'm_musculus'}


class DorinaUtils(object):
    @staticmethod
    def walk_assembly_tree(root, parse_func):
        """Walk a directory structure containg clade, species, assembly

        Call parse_func() for every assembly directory"""
        genomes = {}

        for species in os.listdir(root):
            species_path = os.path.join(root, species)
            if not os.path.isdir(species_path):
                continue

            species_dict = {}

            for assembly in os.listdir(species_path):
                assembly_path = os.path.join(species_path, assembly)
                if not os.path.isdir(assembly_path):
                    continue
                species_dict[assembly] = parse_func(assembly_path)

            # Genomes have description files, regulators don't.
            description_file = os.path.join(species_path, 'description.json')
            try:
                with open(description_file, encoding="utf-8") as fh:
                    genomes[species] = json.load(fh)
                    genomes[species]['assemblies'] = species_dict
            except IOError:
                genomes[species] = species_dict

        return genomes


def urljoin(*args):
    """
    Joins given arguments into a url. Trailing but not leading slashes are
    stripped for each argument.\
    """
    return "/".join([str(x).rstrip('/') for x in args])


def write_file(data, data_path, mode='wb'):
    with open(data_path, mode) as f:  # pragma: no cover
        f.write(data)


def check_file_extension(filename, extension):
    """
    Checks a file for required format.

    :param str filename: Name of the file
    :param str extension: Required extension
    :return bool: whether the filename contains the extension
    """
    return set(filename.split('.')).issuperset(set(extension.split('.')))
    # return extension in filename.replace(ignore, '').rsplit('.', 1)[-1]


def validate_data_path(path_):
    """
    Check whether path is writable

    :param str path_:
    :return str:
    """
    if '~' in path_:
        path_ = path.expanduser(path_)

    if not os.access(path_, os.W_OK):
        log.error('User does not have writing permissions in {}'.format(path_))
    return path_


def uncompress(filename):
    """

    :param str filename:
    :return:
    """
    extension = filename.rsplit('.', 1)[-1]
    uncompressed_filename = filename.replace('.' + extension, '')
    if extension not in ('gz',):
        raise NotImplementedError(
            "Extension {} is unsupported.".format(extension))

    with gzip.open(filename) as _input, \
            open(uncompressed_filename, 'wb') as output:
        shutil.copyfileobj(_input, output)
        shutil.os.remove(filename)

    return uncompressed_filename


def data_for_assembly(assembly, datadir, validate=False, *args):
    from pathlib import Path
    path = Path(datadir, assembly_mapping[assembly], assembly, *args)
    if validate:
        if not path.exists():
            raise TypeError(str(path) + 'is not a valid file.')
    return str(path)

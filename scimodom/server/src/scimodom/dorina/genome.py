#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import unicode_literals
import os
import re
from io import open

from scimodom.dorina.utils import DorinaUtils


class Genome(object):
    _datadir = None
    _genomes = None

    @classmethod
    def init(klass, datadir):
        def parse_func(root):
            """Parse function used to initialise all genomes from the data directory."""

            assembly_dict = {}

            for gff_file in os.listdir(root):
                gff_path = os.path.join(root, gff_file)
                if not os.path.isfile(gff_path):
                    continue

                basename, ext = os.path.splitext(gff_file)
                if ext in ('.gff', '.bed'):
                    assembly_dict[basename] = True

            return assembly_dict

        klass._datadir = datadir
        klass._genomes = DorinaUtils.walk_assembly_tree(
            os.path.join(datadir, 'genomes'),
            parse_func)

    @classmethod
    def all(klass):
        return klass._genomes

    @classmethod
    def path_by_name(klass, name):
        """Take a genome name and return the path to the genome directory"""
        filename = None
        for species, species_dir in list(klass._genomes.items()):
            if name in species_dir['assemblies']:
                filename = os.path.join(klass._datadir, 'genomes', species, name)

        if not filename or not os.path.exists(filename):
            raise ValueError("Could not find genome: %s" % name)

        return filename

    @staticmethod
    def get_genes(name):
        """Get a list of genes from genome <name>"""
        genes = []

        gene_name = re.compile(r'.*ID=(.*?)($|;\w+)')

        genome_dir = Genome.path_by_name(name)
        if genome_dir is None:
            return genes

        genome = os.path.join(genome_dir, 'all.gff')
        if not os.path.exists(genome):
            return genes
        with open(genome, encoding="utf-8") as of:
            for line in of:
                match = gene_name.match(line)
                if match is not None:
                    genes.append(match.group(1))

        return genes

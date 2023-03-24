#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import unicode_literals
import logging
import functools
from os import path

from pybedtools import BedTool

from scimodom.dorina.genome import Genome
from scimodom.dorina.regulator import Regulator

log = logging.getLogger(__name__)

class Dorina(object):
    def __init__(self, datadir, debug=False):
        Genome.init(datadir)
        Regulator.init(datadir)
        
        if debug:
            log.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.INFO)
        
    def analyse(self, genome,
                set_a, match_a='any', region_a='any',
                set_b=None, match_b='any', region_b='any',
                combine='or', genes=None,
                window_a=-1,
                window_b=-1):
        """Run doRiNA analysis"""
        log.debug("analyse(%r, %r(%s) <-'%s'-> %r(%s))" % (
            genome, set_a, match_a, combine, set_b, match_b))

        def compute_result(region, regulators, match, window):
            genome_bed = self._get_genome_bedtool(genome, region, genes)

            # create local copy so we can mangle it
            _regulators = regulators[:]
            if window > -1:
                initial = _regulators.pop(0)
                genome_bed = genome_bed.intersect(initial)
                if window > 0:
                    genome_bed = self._add_slop(genome_bed, genome, window)

            if match == 'any':
                result = genome_bed.intersect(Regulator.merge(_regulators), wa=True, u=True)
            elif match == 'all':
                result = functools.reduce(lambda acc, x: acc.intersect(x, wa=True, u=True),
                                [genome_bed] + _regulators)
            else:
                result = None
            return result

        regulators_a = Regulator.from_names(set_a, assembly=genome)
        regulators_b = Regulator.from_names(set_b, assembly=genome)
        all_regulators = Regulator.merge(regulators_a + regulators_b)

        result_a = compute_result(region_a, regulators_a, match_a, window_a)

        # Combine with set B, if exists
        if set_b:
            result_b = compute_result(region_b, regulators_b, match_b, window_b)
            if combine == 'or':
                combined = Regulator.merge([result_a, result_b])
            elif combine == 'and':
                combined = result_a.intersect(result_b, wa=True, u=True)
            elif combine == 'xor':
                not_in_b = result_a.intersect(result_b, v=True, wa=True)
                not_in_a = result_b.intersect(result_a, v=True, wa=True)
                combined = Regulator.merge([not_in_b, not_in_a])
            elif combine == 'not':
                combined = result_a.intersect(result_b, v=True, wa=True)
        else:
            combined = result_a

        return combined.intersect(all_regulators, wa=True, wb=True)

    def _add_slop(self, feature, genome_name, slop):
        """Add specified slop before and after a regulator"""
        genome = Genome.path_by_name(genome_name)
        chromfile = path.join(genome, "{}.genome".format(genome_name))
        return feature.slop(g=chromfile, b=slop)

    def _get_genome_bedtool(self, genome_name, region, genes=None):
        """get the bedtool object for a genome depending on the name and the region"""
        genome = Genome.path_by_name(genome_name)
        mapping = {"any": "all",
                   "CDS": "cds",
                   "3prime": "3_utr",
                   "5prime": "5_utr",
                   "intron": "intron",
                   "intergenic": "intergenic"}

        if region not in mapping:
            raise ValueError("Invalid region: %r" % region)
        else:
            bed = BedTool(path.join(genome, "%s.gff" % mapping[region]))

        # Optionally, filter by gene.
        if genes is None or 'all' in genes:
            return bed
        else:
            return bed.filter(lambda x: x.name in genes).saveas()

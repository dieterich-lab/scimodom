#!/usr/bin/env python
# -*- coding: utf-8
"""
Created on 09:21 14/02/2018 2018 

"""
import logging

from bioservices import RNASEQ_EBI
from pandas import concat, read_table

log = logging.getLogger(__name__)

retrieve = RNASEQ_EBI()
assembly_to_organism = {'ce6': 'caenorhabditis_elegans',
                        'dm3': "drosophila_melanogaster",
                        'hg19': 'homo_sapiens',
                        'mm9': 'mus_musculus',
                        'mm10': 'mus_musculus',
                        'GRCh38': 'homo_sapiens'}


def retrieve_study(assembly, condition=None):
    """
    Retrieves genes expressed expressed (fpkm > `fpkm_cutoff`) for a given
     `assembly`. Optionally filter for a experimental condition, such as 'heart'

    :param str assembly: Genomic assembly studied
    :param str condition: Experimental condition analysed, for details please
    see https://www.ebi.ac.uk/ols
    :param float fpkm_cutoff: threshold for detecting if a gene is expressed or
    not
    :return list: list of filtered genes
    """

    try:
        organism = assembly_to_organism[assembly]
    except KeyError:
        log.error("Unrecognised assembly %s" % assembly)
        raise

    filtered_studies = retrieve.get_run_by_organism(
        organism=organism, condition=condition)
    filtered_studies = [study for study in filtered_studies if
                        study['ASSEMBLY_USED'] == assembly and
                        study['STATUS'] == 'Complete']
    if condition and not filtered_studies:
        log.error('No studies found with %s condition' % condition)
        raise ValueError
    studies_ids = [study['STUDY_ID'] for study in filtered_studies]

    studies = retrieve.get_studies_by_organism(organism)
    return [study for study in studies if
            study['STUDY_ID'] in studies_ids]


def retrieve_fpkm_from_study(studies):
    try:
        return concat([
            read_table(study['GENES_FPKM_COUNTS_FTP_LOCATION'], index_col=0).T
            for study in studies])
    except ValueError:
        log.error('No suitable data for the provided studies')
        raise


def calculate_expressed_genes(data, fpkm_cutoff=1):
    return data.columns[data.max() > fpkm_cutoff].unique().tolist()


if __name__ == "__main__":
    pass

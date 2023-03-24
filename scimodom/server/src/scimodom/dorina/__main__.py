#!/usr/bin/env python
# -*- coding: utf-8
"""
Created on 16:08 11/10/2017 2017
"""
# pragma: no cover
from __future__ import unicode_literals

import functools
import logging
import os
import sys
from io import open
from subprocess import check_call, Popen

import click

from scimodom.dorina import run as run_dorina
from scimodom.dorina.config import config
from scimodom.dorina.genome import Genome
from scimodom.dorina.regulator import Regulator

# https://stackoverflow.com/a/15729700/1694714
log = logging.getLogger(__name__)
logging.captureWarnings(True)
logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s ')


def call_command(command, stdout=None, cwd=None, mode='w', stdin=None):
    """
    Pipe the output of command to basename in the cwd.

    :param stdin:
    :param str stdout: basename for the output file in cwd.
    :param list command: list of executable plus arguments
    :param cwd: current working directory
    :param mode: mode for file output
    """
    if not isinstance(stdout, str):
        return Popen(command, cwd=cwd, stdout=stdout, stdin=stdin)

    target = os.path.join(cwd, stdout)
    try:
        with open(target, mode=mode) as open_f:
            check_call(command, cwd=cwd, stdout=open_f, stdin=stdin)
    except Exception as e:
        os.remove(target)
        raise e


@click.version_option(version='test', prog_name='dorina')
@click.group(context_settings={'help_option_names': ['-h', '--help']})
def cli():
    """
    This is the command line interface for the doRiNA, a
    database of posttranscriptional regulatory elements
    """
    pass


def common_params(func):
    @click.option('-r', '--release', type=str,
                  default=config.get('DEFAULT', 'version'),
                  help='Ensembl release version', show_default=True)
    @click.option('-o', '--organism',
                  type=str, default=config.get('DEFAULT', 'organism'),
                  help='Organism formal name', show_default=True)
    @click.option('--variation', is_flag=True,
                  help='Retrieves data set from Ensembl variation')
    @click.option('--regulation', is_flag=True,
                  help='Retrieves data set from Ensembl regulation')
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@click.command()
@click.argument('genome')
@click.option('-d', '--debug', is_flag=True,
              help="Set logging level to debug (more verbose)")
@click.option('-a', '--seta', required=True, multiple=True,
              help="First set of regulators to analyse")
@click.option('-b', '--setb',
              help="Second set of regulators to analyse")
@click.option('--genes', multiple=True, default=['all'])
@click.option('--matcha', required=True, type=click.Choice(['any', 'all']),
              show_default=True, default='any',
              help="All or any regulators in set A must match")
@click.option('--regiona', default='any', type=click.Choice(
    ['any', 'CDS', '3prime', '5prime', 'intron', 'intergenic']),
              help="Region to match set A in", show_default=True)
@click.option('--matchb', type=click.Choice(['any', 'all']), default='any',
              help="All or any regulators in set B must match", show_default=True)
@click.option('--regionb', default='any', type=click.Choice(
    ['any', 'CDS', '3prime', '5prime', 'intron', 'intergenic']),
              help="Region to match set B in", show_default=True)
@click.option('-C', '--combine', default='or',
              type=click.Choice(['and', 'or', 'not', 'xor']),
              help="Set operation to combine set A and set B hits")
@click.option('--windowa', type=int, default=-1,
              help="Use windowed search for set A")
@click.option('--windowb', type=int, default=-1,
              help="Use windowed search for set B")
@click.option('--path', '-p', default=config.get('DEFAULT', 'data_path'),
              type=click.Path(exists=True, dir_okay=True, readable=True),
              help="Path to genomes and regulators")
def run(genome, debug, seta, setb, genes, matcha, regiona,
        matchb, regionb, combine, windowa, windowb, path):
    """"Run doRiNA from the command line"""
    
    # no logging...?!
    if debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.ERROR)

    dorina = run_dorina.Dorina(path, debug=debug)
    Genome.init(path)
    mapping = {}
    for x in Genome.all().values():
        for y in x['assemblies']:
            mapping[y] = x['id']
    click.echo('Running DORINA')
    result = dorina.analyse(genome, seta, matcha, regiona, setb, matchb,
                            regionb, combine, genes, windowa, windowb)
    click.echo(result)
    sys.exit(0)


@click.command()
@click.option('--path', '-p', default=config.get('DEFAULT', 'data_path'),
              type=click.Path(exists=True, dir_okay=True, readable=True),
              help="Path to genomes and regulators")
def genomes(path):
    """List available genomes in given directory"""
    Genome.init(path)
    _genomes = Genome

    if _genomes is None:
        click.echo('No genomes available.')
        sys.exit()

    click.echo("Available genomes:")
    click.echo("------------------")
    for species, species_dict in _genomes.all().items():
        click.echo("\t%s" % species)
        for assembly, assembly_dict in species_dict['assemblies'].items():
            click.echo("\t\t%s" % assembly)
            gffs = list(assembly_dict.items())
            gffs.sort(key=lambda x: x[0])
            for gff in gffs:
                click.echo("\t\t\t%s: %s" % gff)
    sys.exit(0)


@click.command()
@click.option('--path', '-p', default=config.get('DEFAULT', 'data_path'),
              type=click.Path(exists=True, dir_okay=True, readable=True),
              help="Path to genomes and regulators")
def regulators(path):
    """List available regulators in a given directory"""
    Regulator.init(path)
    _regulator = Regulator.all()
    if _regulator is None:
        click.echo('No regulators available.')
        sys.exit()

    click.echo("Available regulators:")
    click.echo("---------------------")
    for species, species_dict in _regulator.items():
        click.echo("\t%s" % species)
        for assembly, assembly_dict in species_dict.items():
            click.echo("\t\t%s" % assembly)
            for _regulator, regulator_dict in list(assembly_dict.items()):
                click.echo("\t\t\t%s" % _regulator)
    sys.exit(0)


cli.add_command(regulators)
cli.add_command(genomes)
cli.add_command(run)
if __name__ == '__main__':
    cli()

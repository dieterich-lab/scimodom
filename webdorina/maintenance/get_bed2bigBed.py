#! /usr/bin/env python3

"""Convert BED12+ files to bigBed tracks for visualisation.

Note: Requires the executable "bedToBigBed" and the "chrom.sizes"
      file which can be obtained with the "fetchChromSizes" script.
      The chrom names from the predictions must match those
      of chrom.sizes (UCSC), otherwise they must be re-written by
      passing the right options.

Functions:
    _glob_re
    _read_bed
    _get_bed
    _convert
"""

import sys
import os
import argparse
import logging
import yaml
import json
import csv
import gzip
import re

import pandas as pd

# TODO: temporary
from paths import PROJECT_ROOT
UTILS_PATH = PROJECT_ROOT # / 'utils'

import utils as utils

logger = logging.getLogger(__name__)


# default formatting
AutoSqlStr = '''table bedSourceSelectedFields
"Browser extensible data selected fields."
(
string	chrom;	"Chromosome or scaffold"
uint	chromStart;	"Feature start position on chromosome"
uint	chromEnd;	"Feature end position on chromosome"
string	name;	"Feature id"
uint	score;	"Score"
char[1]	strand;	"+ or -"
uint	thickStart;	"Feature start coordinate"
uint	thickEnd;	"Feature end coordinate"
uint	reserved;	"RGB custom colour scheme"
int	blockCount;	"Number of exons spanned by a feature"
int[blockCount]	blockSizes;	"Comma separated list of exons sizes"
int[blockCount]	chromStarts;	"Start positions of exons relative to chromStart"
)
'''

default_fields = [
    "chrom", "chromStart", "chromEnd", "name", "score", "strand",
    "thickStart", "thickEnd", "itemRgb", "blockCount", "blockSizes", "chromStarts"
]


def _glob_re(pattern, strings):
    return filter(re.compile(pattern).match, strings)


def _read_bed(filename, header, args, sep='\t', **kwargs):
    
    """Reads a BED file into a pandas data frame. This function assumes that 
    field names are prepended with a comment character (see pbio). Otherwise
    a header is added as specified.
    """
    
    if not args.no_header:
        bed = pd.read_csv(filename, sep=sep, **kwargs)
        bed.columns = [c.replace("#", "") for c in bed.columns]
    else: # TODO: this option is not well-defined...
        bed = pd.read_csv(filename, sep=sep, header=None, index_col=False, **kwargs)
        num_columns = len(bed.columns)
        bed.columns = header[:num_columns]
        
    # either way, make sure the first column (chrom) is treated as a string
    chrom_name = bed.columns[0]
    chrom_column = bed[chrom_name]
    bed[chrom_name] = chrom_column.astype(str)

    return bed


def _get_bed(filename, output_filename, fields_to_keep, args):

    """Get BED12+ file and adjust features.
    """
    
    #kwargs = {"comment": "#"}
    kwargs = {}
    if args.skiprows:
        kwargs = {"skiprows": args.skiprows}
    bed = _read_bed(filename, fields_to_keep, args, **kwargs)
    
    # get fields
    header = list(bed.columns)
    chromField = header[0]
    startField = header[1]
    
    # adjust chrom field
    print(args.chr_dict)
    if args.add_chr:
        bed[chromField] = 'chr' + bed[chromField].astype(str)
    if args.chr_dict:
        for chrom_old, chrom_new in args.chr_dict.items():
            seqname_m = bed[chromField] == str(chrom_old)
            bed.loc[seqname_m, chromField] = str(chrom_new)
    if args.chr_file:
        chr_map = pd.read_csv(args.chr_file, 
                              header=None,
                              index_col=0, 
                              squeeze=True).to_dict()
        bed.replace({chromField: chr_map}, inplace=True)

    # sort on the chrom field, and then on the chromStart field.
    bed.sort_values([chromField, startField], ascending=[True, True], inplace=True)

    if args.keep_color:
        # color field must be a string
        pass
    else:
        colorField = header[8]
        bed[colorField] = '64,64,64'

    # remove unused fields
    bed = bed[fields_to_keep]

    # write bed file to output directory
    tmp = os.path.join(args.outputDir, '{}.bed'.format(output_filename))
    if os.path.exists(tmp) and not args.overwrite:
        msg = "Temporary output file {} already exists. Skipping.".format(tmp)
        logger.warning(msg)
    else:
        bed.to_csv(tmp,
                   sep='\t',
                   index=False,
                   header=False,
                   quoting=csv.QUOTE_NONE)
    
    return tmp



def _convert(bed, bb, use_config_fields, args):

    in_files = [bed, args.chrSizes]
    out_files = [bb]
    if use_config_fields:
        cmd = "bedToBigBed -as={} -type={} -extraIndex={} {} {} {}".format(use_config_fields['as_file'],
                                                                           use_config_fields['bed_type'],
                                                                           args.extra_index,
                                                                           bed,
                                                                           args.chrSizes,
                                                                           bb)
        in_files.append(use_config_fields['as_file'])
    else:
        cmd = "bedToBigBed {} {} {}".format(bed, args.chrSizes, bb)

    utils.call_if_not_exists(cmd,
                             out_files,
                             in_files=in_files,
                             overwrite=args.overwrite,
                             call=True)
    if not args.keep:
        try:
            os.remove(bed)
            msg = "Removing: {}".format(bed)
            logger.info(msg)
        except OSError:
            msg = "Could not remove: {}".format(bed)
            logger.info(msg)


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description="""Convert BED to bigBed files by calling 
        the executable program 'bedToBigBed'. The executable must be available on the 
        user's path.""")
    
    parser.add_argument('inputDir', help="""The input directory with BED files, or path to a
        file (txt or yaml) containing full path for each BED file to convert. The input
        format is specified with [--input-format/-fmt]. All BED files MUST have the extension 
        bed or bed.gz if using [--input-format glob], and names are extracted based on this 
        information, unless a yaml file is used, in which case the key:value pair is used 
        to assign names.""")
    
    parser.add_argument('outputDir', help="""The output directory. All BED files are also 
        temporarily re-written to this location.""")

    parser.add_argument('chrSizes', help="The 'chrom.sizes' file for the UCSC database.")


    parser.add_argument('-fmt', '--input-format', help="""The 'type' of input, either 'glob', 
        'txt', or 'yaml' file. With 'glob', regex pattern can be specified with [--pattern].
        With 'yaml', the key must be specified with [--key].""", type=str, 
        choices=['glob', 'txt', 'yaml'], default='glob')

    parser.add_argument('--pattern', help="""A comma-separated list of patterns used to glob
        BED files.""", default='', type=str, nargs='*')
    
    parser.add_argument('--key', help="""The key to access the list of files if using
        a yaml input file.""", default='samples', type=str)
    
    parser.add_argument('--skip', help="""If this flag is present then temporary BED files
        are not generated, and the input BED files are converted directly. There is no format
        check! Options/flags such as [--add-chr, --chr-dict, --chr-file, --keep-color, 
        --no-header] are ignored.""", action='store_true')

    parser.add_argument('--no-header', help="""Use this flag if input BED files have no
        header. Standard BED12 fields are used if [--configure-fields] is not given.""", 
        action='store_true')
    
    #parser.add_argument('--no-color', help="""BED6 (tmp)""", action='store_true')
    # --keep-color
    
    parser.add_argument('--skiprows', help="""Pass to pandas.read_csv.""", 
        type=int)
    
    parser.add_argument('--add-chr', help="""If this flag is present then 'chr' will be pre-pended
        to sequence names. This is done before any other changes to sequence names, so this
        must be taken into account if giving a dictionary mapping.""", action='store_true')

    parser.add_argument('--chr-dict', help="""A dictionary mapping of sequence names found
        in the data to the sequence names, as in "chrom.sizes". The format is as follows:
        '{"key/old":"value/new"}'""", type=json.loads)

    parser.add_argument('--chr-file', help="""A dictionary mapping of sequence names to 
        the sequence names, as in "chrom.sizes", given as a CSV file without header: old,new.
        The file can contain any association, only those in the data will be used.""")

    # TODO: [--configure-field] may not be required, and default file may be enough...
    parser.add_argument('--extra-index', help="""A comma-separated string of fields to which 
        an index is added, passed to bedToBigBed -extraIndex. The [--configure-field] 
        option is required""", default='name', type=str)

    parser.add_argument('--keep-color', help="""If this flag is present then color fields 
        present in the original BED files are used (string), otherwise a uniform grey color 
        is used for al files. The [--configure-field] option is required.""", action='store_true')
    
    parser.add_argument('-asf', '--configure-fields', help="""A file with comma-separated items
        (one per line) corresponding to fields that will be included in the bigBed file. The field 
        names must correspond to the ones used the BED file. Each field name must be followed by
        'type', 'standard field name', 'description', as needed to generate the AutoSql format (.as)
        file describing these fields. Standard fields must be separated from any extra fields
        by an empty line. See e.g. https://genome.ucsc.edu/goldenpath/help/bigBed.html.
        One extra index will be created on the name field by default. If multiple BED files are
        passed in, these will be used for all input files. If unused, a default file will be 
        generated using the 'standard' field names for BED12.""", 
        required=any(item in ['--keep-color', '--extra-index'] for item in sys.argv))

    utils.add_file_options(parser)
    utils.add_logging_options(parser)
    args = parser.parse_args()
    utils.update_logging(args)
    
    msg = "[get-bed2bigBed]: {}".format(' '.join(sys.argv))
    logger.info(msg)
    
    # check that stand-alone executable(s) are callable
    programs = ['bedToBigBed']
    utils.check_programs_exist(programs)
    
    # check output path
    if os.path.exists(args.outputDir):
        args.outputDir = os.path.join(args.outputDir, '')
    else:
        msg = "Invalid output path or wrong permission: {}. Terminating.".format(args.outputDir)
        raise OSError(msg)    
    
    # input format - fetch BED files
    if args.input_format == 'glob': 
        filenames = list(_glob_re(r'.*(bed|bed.gz)', os.listdir(args.inputDir)))
        match = r'.*({}).*'.format('|'.join(args.pattern))
        filenames = list(_glob_re(match, filenames))
        filenames = [os.path.join(args.inputDir, f) for f in filenames]
    elif args.input_format == 'txt':
        filenames = pd.read_csv(args.inputDir,
                                header=None,
                                usecols=[0],
                                names=['f']).f.to_list()
    elif args.input_format == 'yaml':
        config = yaml.load(open(args.inputDir), Loader=yaml.FullLoader)
        try:
            filenames = list(config[args.key].values())
            fileMapping = config[args.key]
        except:
            msg = 'Missing/wrong key: [--input-format yaml] but [--key] is wrong!'
            raise KeyError(msg)
            
    if not args.input_format == 'yaml':
        fileMapping = {}
        for f in filenames:
            # TODO: interaction POSIX - Windows styled path...?
            outputFile = os.path.basename(f)
            if outputFile.endswith('gz'):
                outputFile = os.path.splitext(os.path.splitext(outputFile)[0])[0]
            else:
                outputFile = os.path.splitext(outputFile)[0]
            fileMapping[outputFile] = f
            
    # generate an AutoSql format (.as) file describing the fields
    as_file = args.outputDir + 'SelectedFields.as'
    use_config_fields = {}
    use_config_fields['as_file'] = as_file
    if args.configure_fields:
        msg = "Configuring fields using {}.".format(args.configure_fields)
        logger.info(msg)
        fields_to_keep = []
        extra_fields = []
        f = open(args.configure_fields, 'r')
        lines = f.readlines()
        f.close()
        f = open(str(as_file), 'w')
        f.write("{} {}\n".format("table", "bedSourceSelectedFields"))
        f.write('''"{}"\n'''.format("Browser extensible data selected fields."))
        f.write("{}\n".format("("))
        n_fields = 0
        for line_no, line in enumerate(lines):
            l = line.strip()
            if not l:
                n_fields = line_no
                break
            fields = l.split(',')
            fields_to_keep.append(fields[0])
            f.write("{}\t{};\t{}\n".format(fields[1], fields[2], fields[3]))
        bed_type = "bed" + str(len(fields_to_keep))
        if n_fields:
            for line in lines[n_fields+1:]:
                l = line.strip()
                fields = l.split(',')
                extra_fields.append(fields[0])
                f.write("{}\t{};\t{}\n".format(fields[1], fields[2], fields[3]))
            bed_type += "+" + str(len(extra_fields))
            fields_to_keep += extra_fields
        f.write("{}\n".format(")"))
        f.close()
        use_config_fields['bed_type'] = bed_type
    else:
        msg = """Using default fields for BED12."""
        logger.info(msg)
        with open(as_file, "w") as f:
            f.write(f'{AutoSqlStr}')
        use_config_fields['bed_type'] = 'bed12'
        fields_to_keep = default_fields
        
    # convert to bigBed directly...
    if args.skip:
        msg = """Using [--skip] and directly converting input files!"""
        for newBed, oldBed in fileMapping.items():
            if not os.path.exists(oldBed):
                msg = "Could not find the BED file: {}. Terminating.".format(oldBed)
                raise FileNotFoundError(msg)
            _convert(oldBed, 
                     os.path.join(args.outputDir, '{}.bb'.format(newBed)), 
                     use_config_fields, 
                     args)
    #... or prepare BED files prior to convert to bigBed.
    else:
        for newBed, oldBed in fileMapping.items():
            if not os.path.exists(oldBed):
                msg = "Could not find the BED file: {}. Terminating.".format(oldBed)
                raise FileNotFoundError(msg)
            filename = _get_bed(oldBed, newBed, fields_to_keep, args)
            _convert(filename, 
                     os.path.join(args.outputDir, '{}.bb'.format(newBed)), 
                     use_config_fields, 
                     args)


if __name__ == '__main__':
    main()

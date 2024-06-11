"""pybedtools
"""

from collections.abc import Sequence
from os import makedirs
import logging
from pathlib import Path
import shlex
import subprocess
from typing import Any

import pybedtools  # type: ignore

from scimodom.config import Config

logger = logging.getLogger(__name__)


_tempdir = Config.BEDTOOLS_TMP_PATH
makedirs(_tempdir, exist_ok=True)
pybedtools.helpers.set_tempdir(_tempdir)


def to_bedtool(records, as_list: bool = False):
    """Convert records to BedTool and sort

    TODO: records can be str | Path | Sequence[Any], see below get_genomic_annotation!
    check https://daler.github.io/pybedtools/autodocs/pybedtools.bedtool.BedTool.html
    For testing, should we allow passing from_string?

    :param records: Database records (or list of records)
    :type records: Sequence
    :param as_list: Return results as a list of BedTool
    :type as_list: bool
    :return: bedtool
    :rtype: BedTool or list of BedTool
    """
    if as_list:
        bedtool = [pybedtools.BedTool(record).sort() for record in records]
    else:
        bedtool = pybedtools.BedTool(records).sort()
    return bedtool


def liftover_to_file(
    records: list[tuple[Any, ...]],
    chain_file: str,
    unmapped: str | None = None,
    chrom_id: str = "s",
) -> tuple[str, str]:
    """Liftover records. Handles conversion to BedTool, but not from,
    of the liftedOver features. A file is returned pointing
    to the liftedOver features. The unmapped ones are saved as
    "unmapped", or discarded.

    :param records: Data records to liftover
    :type records: List of tuple of (str, ...) - Data records
    :param chain_file: Chain file
    :type chain_file: str
    :param unmapped: File to write unmapped features
    :type unmapped: str or None
    :param chrom_id: The style of chromosome IDs (default s).
    :type chrom_id: str
    :returns: Files with liftedOver and unmapped features
    :rtype: tuple of (str, str)
    """
    bedtool = to_bedtool(records)
    result = pybedtools.BedTool._tmp()
    if unmapped is None:
        unmapped = pybedtools.BedTool._tmp()
    cmd = f"CrossMap bed --chromid {chrom_id} --unmap-file {unmapped} {chain_file} {bedtool.fn} {result}"

    logger.debug(f"Calling: {cmd}")

    # set a timeout?
    try:
        subprocess.run(shlex.split(cmd), check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        msg = "Process failed: CrossMap executable could not be found!"
        raise Exception(msg) from exc
    except subprocess.CalledProcessError as exc:
        msg = f"Process failed with {exc.stderr}"
        raise Exception(msg) from exc
    # except subprocess.TimeoutExpired as exc:
    return result, unmapped

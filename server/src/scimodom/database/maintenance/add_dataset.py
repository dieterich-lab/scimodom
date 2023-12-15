#! /usr/bin/env python3

"""Maintenance script for the DataService utility.
This script allows to create a new dataset for an existing
project.
"""

import logging

import scimodom.utils.utils as utils
import scimodom.database.queries as queries

from pathlib import Path
from sqlalchemy import select
from argparse import ArgumentParser, SUPPRESS

from scimodom.config import Config
from scimodom.database.database import make_session
from scimodom.services.dataset import DataService
from scimodom.services.annotation import AnnotationService
from scimodom.database.models import (
    Project,
    Taxa,
    Assembly,
    Modomics,
    Modification,
    DetectionTechnology,
    Organism,
    Selection,
)

logger = logging.getLogger(__name__)


def main():
    parser = ArgumentParser(
        add_help=False,
        description="""Add new dataset to DB for SMID - create EUFID. Project should exists, incl. default setup.""",
    )

    required = parser.add_argument_group("required arguments")
    optional = parser.add_argument_group("optional arguments")

    optional.add_argument(
        "-db",
        "--database",
        help="Database URI",
        type=str,
        default=Config.DATABASE_URI,
    )

    required.add_argument(
        "-smid",
        "--project-id",
        help="""Existing project ID (SMID)""",
        type=str,
        required=True,
    )

    required.add_argument(
        "--title",
        help="""Dataset title""",
        type=str,
        required=True,
    )

    required.add_argument(
        "--file",
        help="""Path to bedRMod file""",
        type=str,
        required=True,
    )

    optional.add_argument(
        "-h",
        "--help",
        action="help",
        default=SUPPRESS,
        help="show this help message and exit",
    )

    optional.add_argument(
        "-o",
        "--organism",
        help="""NCBI Taxa ID""",
        type=int,
    )

    optional.add_argument(
        "-a",
        "--assembly",
        help="""Valid name of assembly""",
        type=str,
    )

    optional.add_argument(
        "-m",
        "--modification",
        help="""Valid names of modifications (MODOMICS short name or MODOMICS ID if [--modomics])""",
        nargs="+",
        type=str,
    )

    optional.add_argument(
        "--modomics",
        help="""Use MODOMICS ID for [--modification]""",
        action="store_true",
    )

    optional.add_argument(
        "-rna",
        "--rna-type",
        help="""Valid name of RNA type, must match [--modification]""",
        nargs="+",
        type=str,
        choices=["mRNA", "rRNA", "tRNA"],  # TODO: FIX/UPDATE
    )

    optional.add_argument(
        "-t",
        "--technology",
        help="""Valid name of technology. Name must be unique wrt to method, otherwise use [--technology-id]""",
        type=str,
    )

    optional.add_argument(
        "-cto",
        "--cell-type",
        help="""Valid name of cell, tissue, or organism, matched with [--organism]""",
        type=str,
    )

    optional.add_argument(
        "--assembly-id",
        help="""Assembly ID. If given, overrides [--assembly]""",
        type=int,
    )

    optional.add_argument(
        "--modification-id",
        help="""Modification ID. If given, overrides [--modification] and [--rna-type]""",
        nargs="+",
        type=int,
    )

    optional.add_argument(
        "--technology-id",
        help="""Technology ID. If given, overrides [--technology]""",
        type=int,
    )

    optional.add_argument(
        "--cto-id", help="""Organism ID. If given, overrides [--organism]""", type=int
    )

    utils.add_log_opts(parser)
    args = parser.parse_args()
    utils.update_logging(args)

    engine, session_factory = make_session(args.database)
    session = session_factory()
    # do quite a bit of validation...

    # is SMID valid?
    try:
        smid = session.execute(
            select(Project.id).where(Project.id == args.project_id)
        ).one()
    except:
        msg = f"Given project ID SMID={args.project_id} not found! Terminating!"
        logger.error(msg)
        return
    smid = smid[0]

    # input file
    if not Path(args.file).is_file():
        msg = (
            f"Given input file={args.file} not found, or not a valid file! Terminating!"
        )
        logger.error(msg)
        return
    handle = open(args.file, "r")

    # is organism valid?
    try:
        taxa_id = session.execute(select(Taxa.id).where(Taxa.id == args.organism)).one()
    except:
        msg = f"Given organism Taxa ID={args.organism} not found! Terminating!"
        logger.error(msg)
        return
    taxa_id = taxa_id[0]

    # is assembly valid?
    if args.assembly_id:
        ids = session.execute(select(Assembly.id)).scalars().all()
        if args.assembly_id not in ids:
            msg = f"Given assembly ID {args.assembly} not found! Terminating!"
            logger.error(msg)
            return
        assembly_id = args.assembly_id
    else:
        try:
            assembly_id = session.execute(
                select(Assembly.id).where(
                    Assembly.name == args.assembly, Assembly.taxa_id == taxa_id
                )
            ).one()
            assembly_id = assembly_id[0]
        except:
            msg = f"Given assembly {args.assembly} with taxa ID={taxa_id} not found! Terminating!"
            logger.error(msg)
            return

    # are modifications valid?
    if args.modification_id:
        ids = session.execute(select(Modification.id)).scalars().all()
        if not all(m in ids for m in args.modification_id):
            msg = f"Some modification IDs {args.modification_id} were not found! Terminating!"
            logger.error(msg)
            return
        modification_ids = args.modification_id
    else:
        if len(args.modification) != len(args.rna_type):
            msg = "Number of [--modification] must match number of [--rna-type]! Terminating!"
            logger.error(msg)
            return
        modification_ids = []
        for modification, rna in zip(args.modification, args.rna_type):
            try:
                if args.modomics:
                    modomics_id = modification
                else:
                    modomics_id = session.execute(
                        select(Modomics.id).where(Modomics.short_name == modification)
                    ).scalar()
                modification_id = session.execute(
                    select(Modification.id).where(
                        Modification.modomics_id == modomics_id,
                        Modification.rna == rna,
                    )
                ).one()
                modification_ids.append(modification_id[0])
            except:
                msg = f"Modification {modification} (RNA type = {rna}) not found! Terminating!"
                logger.error(msg)
                return

    # is technology valid?
    # in principle if same tech with 2 meth, one() should raise an error...
    if args.technology_id:
        ids = session.execute(select(DetectionTechnology.id)).scalars().all()
        if args.technology_id not in ids:
            msg = f"Technology ID {args.technology_id} not found! Terminating!"
            logger.error(msg)
            return
        technology_id = args.technology_id
    else:
        try:
            technology_id = session.execute(
                select(DetectionTechnology.id).where(
                    DetectionTechnology.tech == args.technology
                )
            ).one()
            technology_id = technology_id[0]
        except:
            msg = f"Given technology {args.technology} not found, or ambiguous selection due to method! Terminating!"
            logger.error(msg)
            return

    # is technology valid?
    # in principle if same tech with 2 meth, one() should raise an error...
    if args.cto_id:
        ids = session.execute(select(Organism.id)).scalars().all()
        if args.cto_id not in ids:
            msg = f"Organism ID {args.cto_id} not found! Terminating!"
            logger.error(msg)
            return
        cto_id = args.cto_id
    else:
        try:
            cto_id = session.execute(
                select(Organism.id).where(
                    Organism.cto == args.cell_type,
                    Organism.taxa_id == taxa_id,
                )
            ).one()
            cto_id = cto_id[0]
        except:
            msg = f"Given cell type {args.cell_type} for Taxa ID {taxa_id} not found! Terminating!"
            logger.error(msg)
            return

    # double check, are selections valid?
    for idx in modification_ids:
        try:
            selection_id = session.execute(
                select(Selection.id).where(
                    Selection.modification_id == idx,
                    Selection.technology_id == technology_id,
                    Selection.organism_id == cto_id,
                )
            ).one()
        except:
            msg = "Given selection not found! Terminating!"
            logger.error(msg)
            return

    # call
    service = DataService(
        session,
        smid,
        args.title,
        args.file,
        handle,
        taxa_id,
        assembly_id,
        modification_ids,
        technology_id,
        cto_id,
    )

    query = queries.query_column_where(Taxa, "name", filters={"id": taxa_id})
    organism = session.execute(query).scalar()
    query = queries.query_column_where(Assembly, "name", filters={"id": assembly_id})
    assembly = session.execute(query).scalar()
    modifications = []
    for idx in modification_ids:
        records = session.execute(
            select(Modification).where(Modification.id == idx)
        ).scalar()
        modifications.append(f"{records.modomics_id} ({records.rna})")
    query = queries.query_column_where(
        DetectionTechnology, "tech", filters={"id": technology_id}
    )
    technology = session.execute(query).scalar()
    query = queries.query_column_where(Organism, "cto", filters={"id": cto_id})
    cto = session.execute(query).scalar()

    msg = (
        f"Adding dataset for Taxa ID={organism}; Assembly={assembly}; Modifications={', '.join(modifications)}; "
        f"Technology={technology}; and Cell/Tissue/Organ={cto} to project {smid} from {args.file}..."
    )
    if not utils.confirm(msg):
        return
    eufid = service.create_dataset()

    service = AnnotationService(session, eufid=eufid)
    service.annotate_data()


if __name__ == "__main__":
    main()

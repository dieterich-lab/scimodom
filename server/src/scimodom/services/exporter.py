#
# The purpose of this module is to write bedRMod files
#
from logging import getLogger
from typing import TextIO

from sqlalchemy import select
from sqlalchemy.orm import Session

from scimodom.database.models import (
    Dataset,
    Association,
    Selection,
    Data,
    DetectionTechnology,
    DetectionMethod,
)

logger = getLogger(__name__)


def _or_default(value, default):
    return default if value is None else value


class Exporter:
    def __init__(self, session: Session):
        self._session = session

    def export_dataset(self, dataset_id: str, stream: TextIO):
        dataset = self._session.get(Dataset, dataset_id)
        db = self._session
        associations = list(
            db.scalars(select(Association).where(Association.dataset_id == dataset.id))
        )
        self._write_header(dataset, stream, associations)
        self._write_records(associations, stream)

    def _write_header(self, dataset, stream, associations):
        db = self._session
        if len(associations) > 1:
            logger.warning(
                f"WARNING: Dataset {dataset.id} has multiple associations - just using the first for the header."
            )
        selection_ids = [a.selection_id for a in associations]
        selections = list(
            db.scalars(select(Selection).where(Selection.id.in_(selection_ids)))
        )
        taxa_id = self._get_taxa_id_from_selections(dataset, selections)
        assembly = "TODO"  # We might get one via selection.inst_organism.inst_taxa.assemblies - but which?
        annotation_source = "TODO"
        annotation_version = "TODO"

        stream.write(
            f"""#fileformat=bedRModv1.7
#organism={taxa_id}
#modification_type={dataset.modification_type}
#assembly={assembly}
#annotation_source={annotation_source}
#annotation_version={annotation_version}
#sequencing_platform={_or_default(dataset.sequencing_platform, '')}
#basecalling={_or_default(dataset.basecalling, '')}
#bioinformatics_workflow={_or_default(dataset.bioinformatics_workflow, '')}
#experiment={_or_default(dataset.experiment, '')}
#external_source={_or_default(dataset.external_source, '')}
#om\tomStart\tomEnd\tname\tscore\tstrand\tthickStart\tthickEnd\titemRgb\tcoverage\tfrequency
"""
        )

    @staticmethod
    def _get_taxa_id_from_selections(dataset, selections):
        candidates = [s.inst_organism.taxa_id for s in selections]
        for i in candidates[1:]:
            if candidates[0] != i:
                logger.warning(
                    f"Found inconsistent Taxa IDs in data set {dataset.id} ({', '.join(str(candidates))})"
                )
        return candidates[0]

    def _write_records(self, associations, stream):
        db = self._session
        association_ids = [a.id for a in associations]
        for data in db.scalars(
            select(Data).where(Data.association_id.in_(association_ids))
        ):
            parts = [
                data.chrom,
                str(data.start),
                str(data.end),
                data.name,
                str(data.score),
                data.strand,
                str(data.thick_start),
                str(data.thick_end),
                data.item_rgb,
                str(data.coverage),
                str(data.frequency),
            ]
            print("\t".join(parts), file=stream)

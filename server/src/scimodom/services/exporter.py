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
    AssemblyVersion,
    Assembly,
    AnnotationVersion,
    Annotation,
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
        self._write_header(dataset, associations, stream)
        self._write_records(associations, stream)

    def _write_header(self, dataset, associations, stream):
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
        assembly = self._get_assembly(taxa_id)
        annotation_version = self._get_annotation_version(taxa_id)

        stream.write(
            f"""#fileformat=bedRModv1.7
#organism={taxa_id}
#modification_type={dataset.modification_type}
#assembly={assembly}
#annotation_source=Ensembl
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

    def _get_assembly(self, taxa_id):
        db = self._session
        assembly_version = list(db.scalars(select(AssemblyVersion)))[0].version_num
        candidates = list(
            db.scalars(
                select(Assembly).where(
                    Assembly.version == assembly_version, Assembly.taxa_id == taxa_id
                )
            )
        )
        if len(candidates) > 1:
            logger.warning(
                f"WARNING: Found multiple Assemblies for taxa_id {taxa_id} and Assembly version {assembly_version}!"
            )
        return candidates[0].name

    def _get_annotation_version(self, taxa_id):
        db = self._session
        annotation_version = list(db.scalars((select(AnnotationVersion))))[
            0
        ].version_num
        candidates = list(
            db.scalars(
                select(Annotation).where(
                    Annotation.version == annotation_version,
                    Annotation.taxa_id == taxa_id,
                )
            )
        )
        if len(candidates) > 1:
            logger.warning(
                f"WARNING: Found multiple Annotation for taxa_id {taxa_id} and Annotation version {annotation_version}!"
            )
        return candidates[0].release

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

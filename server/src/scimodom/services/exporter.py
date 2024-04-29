#
# The purpose of this module is to write .bedrmod files
#
from logging import getLogger
import re
from typing import Optional, Generator

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
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
from scimodom.utils.specifications import SPECS_EUF

logger = getLogger(__name__)


def _or_default(value, default):
    return default if value is None else value


class NoSuchDataset(Exception):
    pass


class Exporter:
    BAD_FILE_NAME_CHARACTERS_REGEXP = re.compile(r"[^a-zA-Z0-9(),._-]")
    VERSION = SPECS_EUF["versions"][-1]

    def __init__(self, session: Session):
        self._session = session

    def get_dataset_file_name(self, dataset_id: str) -> str:
        try:
            dataset = self._session.get_one(Dataset, dataset_id)
        except NoResultFound:
            raise NoSuchDataset(f"Failed to find dataset {dataset_id}")
        cleaned_name = re.sub(self.BAD_FILE_NAME_CHARACTERS_REGEXP, "_", dataset.title)
        return f"{cleaned_name}.bedrmod"  # noqa

    def generate_dataset(self, dataset_id: str) -> Generator[bytes, None, None]:
        try:
            dataset = self._session.get_one(Dataset, dataset_id)
        except NoResultFound:
            raise NoSuchDataset(f"Failed to find dataset {dataset_id}")
        db = self._session
        associations = list(
            db.scalars(select(Association).where(Association.dataset_id == dataset.id))
        )
        for line in self._generate_header(dataset, associations):
            yield line.encode("utf-8")
        for line in self._generate_records(associations):
            yield line.encode("utf-8")

    def _generate_header(self, dataset, associations):
        db = self._session
        if len(associations) > 1:
            logger.warning(
                f"WARNING: Dataset {dataset.id} has multiple associations - just using the first for the header."
            )
        selection_ids = [a.selection_id for a in associations]
        selections = list(
            db.scalars(select(Selection).where(Selection.id.in_(selection_ids)))
        )

        yield f"#fileformat=bedRModv{self.VERSION}\n"  # noqa
        taxa_id = self._get_taxa_id_from_selections(dataset, selections)
        yield f"#organism={taxa_id}\n"
        yield f"#modification_type={dataset.modification_type}\n"
        assembly = self._get_assembly(taxa_id)
        yield f"#assembly={assembly}\n"
        yield "#annotation_source=Ensembl\n"
        annotation_version = self._get_annotation_version(taxa_id)
        yield f"#annotation_version={annotation_version}\n"
        yield f"#sequencing_platform={_or_default(dataset.sequencing_platform, '')}\n"
        yield f"#basecalling={_or_default(dataset.basecalling, '')}\n"
        yield f"#bioinformatics_workflow={_or_default(dataset.bioinformatics_workflow, '')}\n"
        yield f"#experiment={_or_default(dataset.experiment, '')}\n"
        yield f"#external_source={_or_default(dataset.external_source, '')}\n"
        yield "#chrom\tchromStart\tchromEnd\tname\tscore\tstrand\tthickStart\tthickEnd\titemRgb\tcoverage\tfrequency\n"

    @staticmethod
    def _get_taxa_id_from_selections(dataset, selections):
        candidates = [s.inst_organism.taxa_id for s in selections]
        for i in candidates[1:]:
            if candidates[0] != i:
                logger.warning(
                    f"WARNING: Found inconsistent Taxa IDs in data set {dataset.id} ({', '.join(str(candidates))})"
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

    def _generate_records(self, associations):
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
            yield "\t".join(parts) + "\n"


_cached_exporter: Optional[Exporter] = None


def get_exporter() -> Exporter:
    global _cached_exporter
    if _cached_exporter is None:
        _cached_exporter = Exporter(session=get_session())
    return _cached_exporter

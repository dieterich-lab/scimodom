#
# The purpose of this module is to write .bedrmod files
#
import logging
import re
from typing import Optional, Generator

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import (
    Dataset,
    Data,
    Assembly,
    Annotation,
)
import scimodom.database.queries as queries
from scimodom.utils.specifications import SPECS_EUF


logger = logging.getLogger(__name__)


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
        for line in self._generate_header(dataset):
            yield line.encode("utf-8")
        for line in self._generate_records(dataset):
            yield line.encode("utf-8")

    def _get_assembly(self, taxa_id) -> str:
        """Retrieve the current assembly for this Taxa ID.

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :returns: Assembly name
        :rtype: str
        """
        query = queries.get_assembly_version()
        version = self._session.execute(query).scalar_one()
        query = queries.query_column_where(
            Assembly, "name", filters={"taxa_id": taxa_id, "version": version}
        )
        return self._session.execute(query).scalar_one()

    def _get_annotation_version(self, taxa_id) -> int:
        """Retrieve the current annotation for this Taxa ID.

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :returns: Annotation release
        :rtype: int
        """
        query = queries.get_annotation_version()
        version = self._session.execute(query).scalar_one()
        query = queries.query_column_where(
            Annotation, "release", filters={"taxa_id": taxa_id, "version": version}
        )
        return self._session.execute(query).scalar_one()

    def _generate_header(self, dataset: Dataset):
        """Generate dataset header.

        :param dataset: Dataset
        :type dataset: Dataset
        """
        yield f"#fileformat=bedRModv{self.VERSION}\n"  # noqa
        taxa_id = dataset.inst_organism.taxa_id
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

    def _generate_records(self, dataset: Dataset):
        """Generate data records.

        :param dataset: Dataset
        :type dataset: Dataset
        """
        for data in self._session.scalars(
            select(Data).where(Data.dataset_id == dataset.id)
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

import logging
import shutil
from pathlib import Path
from typing import ClassVar, Callable
from posixpath import join as urljoin

from scimodom.database.buffer import InsertBuffer
from scimodom.database.models import Annotation, DataAnnotation, GenomicAnnotation
from scimodom.services.annotation.generic import GenericAnnotationService
import scimodom.utils.specifications as specs
from scimodom.services.file import AssemblyFileType

logger = logging.getLogger(__name__)


class EnsemblAnnotationService(GenericAnnotationService):
    """Utility class to handle Ensembl annotation.

    :params FMT: Annotation file format
    :type FMT: str
    :param ANNOTATION_FILE: Annotation file name
    :type ANNOTATION_FILE: Callable
    :param FEATURES: Genomic features
    :type FEATURES: dict of {str: dict of {str: str}}
    """

    FMT: ClassVar[str] = "gtf"  # only handles GTF
    ANNOTATION_FILE: ClassVar[
        Callable
    ] = "{organism}.{assembly}.{release}.chr.{fmt}.gz".format
    FEATURES: ClassVar[dict[str, dict[str, str]]] = {
        "conventional": {
            "exon": "Exonic",
            "five_prime_utr": "5'UTR",
            "three_prime_utr": "3'UTR",
            "CDS": "CDS",
        },
        "extended": {"intron": "Intronic", "intergenic": "Intergenic"},
    }

    def get_annotation(self, taxa_id: int) -> Annotation:
        """Retrieve annotation from taxonomy ID.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :returns: Annotation instance
        :rtype: Annotation

        :raises: AnnotationNotFoundError
        """
        return self.get_annotation_from_taxid_and_source(taxa_id, "ensembl")

    def create_annotation(self, taxa_id: int, **kwargs) -> None:
        """This method automates the creation of Ensembl
        annotations for a given organism for the current
        release. The annotation must exist in the database.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        """
        annotation = self.get_annotation(taxa_id)
        if self._release_exists(annotation.id):
            return

        release_path = self.get_release_path(annotation)
        annotation_file, url = self._get_annotation_paths(annotation, release_path)
        chrom_file = self._file_service.get_assembly_file_path(
            annotation.taxa_id, AssemblyFileType.CHROM
        )

        logger.info(
            f"Setting up Ensembl {annotation.release} for {annotation.taxa_id}..."
        )

        try:
            release_path.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            exc.add_note(f"... but no records found for annotation {annotation.id}.")
            raise

        try:
            with open(annotation_file, "wb") as fh:
                self._web_service.stream_request_to_file(url, fh)
            self._bedtools_service.ensembl_to_bed_features(
                annotation_file,
                chrom_file,
                {k: list(v.keys()) for k, v in self.FEATURES.items()},
            )
            self._update_database(annotation.id, annotation_file)
            self._session.commit()
        except Exception:
            self._session.rollback()
            shutil.rmtree(release_path)
            raise

    def _annotate_data_in_database(self, taxa_id: int, eufid: str) -> None:
        """Annotate Data: add entries to DataAnnotation
        for a given dataset.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :param eufid: EUF ID
        :type eufid: str
        """
        annotation = self.get_annotation(taxa_id)
        release_path = self.get_release_path(annotation)

        logger.debug(f"Annotating records for EUFID {eufid}...")

        records = list(self._data_service.get_by_dataset(eufid))

        features = {**self.FEATURES["conventional"], **self.FEATURES["extended"]}
        annotated_records = self._bedtools_service.annotate_data_using_ensembl(
            release_path, features, records
        )
        with InsertBuffer[DataAnnotation](self._session) as buffer:
            for record in annotated_records:
                buffer.queue(DataAnnotation(**record.model_dump()))

    def _update_database(self, annotation_id: int, annotation_file: Path) -> None:
        records = self._bedtools_service.get_ensembl_annotation_records(
            annotation_file,
            annotation_id,
            self.FEATURES["extended"]["intergenic"],
        )
        with InsertBuffer[GenomicAnnotation](self._session) as buffer:
            for record in records:
                buffer.queue(GenomicAnnotation(**record.model_dump()))

    def _get_annotation_paths(
        self, annotation: Annotation, release_path: Path
    ) -> tuple[Path, str]:
        filen = self.ANNOTATION_FILE(
            organism=release_path.parent.parent.name,
            assembly=release_path.parent.name,
            release=annotation.release,
            fmt=self.FMT,
        )
        url = urljoin(
            specs.ENSEMBL_FTP,
            f"release-{annotation.release}",
            self.FMT,
            release_path.parent.parent.name.lower(),
            filen,
        )
        return Path(release_path, filen), url

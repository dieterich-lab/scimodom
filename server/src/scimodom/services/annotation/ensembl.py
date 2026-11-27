"""Classes and methods for Ensembl annotations."""

import logging
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar

from scimodom.database.buffer import InsertBuffer
from scimodom.database.models import (
    Annotation,
    DataAnnotation,
    GenomicAnnotation,
)
from scimodom.services.annotation.generic import GenericAnnotationService
from scimodom.services.ensembl import EnsemblAssemblyClient
from scimodom.utils.specs.enums import AnnotationSource, AssemblyFileType

logger = logging.getLogger(__name__)


class EnsemblAnnotationService(GenericAnnotationService):
    """Utility class to handle Ensembl annotation.

    :param ensembl_client: Ensembl assembly client (owns
    the Ensembl URL layout)
    :params FMT: Annotation file format
    :param ANNOTATION_FILE: Annotation file name
    :param FEATURES: Genomic features
    """

    ANNOTATION_SOURCE: ClassVar[str] = AnnotationSource.ENSEMBL.value
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
    # TODO: organisms served without the ".chr" variant, cf. #149
    NO_CHR_VARIANT_TAXA: ClassVar[list[int]] = [4932, 6239]

    def __init__(
        self,
        ensembl_client: EnsemblAssemblyClient,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._ensembl_client = ensembl_client

    def get_current(self, taxa_id: int) -> Annotation:
        """Retrieve the current annotation.

        :param taxa_id: NCBI taxon
        :raise: AnnotationNotFoundError
        :return: Annotation instance
        """
        return self.get_current_by_taxa_and_source(
            taxa_id,
            self.ANNOTATION_SOURCE,
        )

    def get_annotations(
        self,
        taxa_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get the current Ensembl annotations.

        This adds the browser page of the archive the
        release is served from. A record annotated here
        is browsed at the release it was annotated with.

        :param taxa_id: NCBI taxon or None
        :return: JSON array with extended annotations
        """
        annotations = super().get_annotations(taxa_id)
        for annotation in annotations:
            annotation["browse_url"] = self._ensembl_client.get_browse_url(
                annotation["archive"], annotation["taxa_name"]
            )
        return annotations

    def create_current_annotation(self, taxa_id: int, **kwargs) -> None:
        """Create the current Ensembl annotation of a taxon.

        :param taxa_id: NCBI taxon
        """
        annotation = self.get_current(taxa_id)
        if self._has_records(annotation):
            return

        assembly = annotation.inst_assembly
        release_path = self.get_release_path(annotation)
        annotation_file, url = self._get_annotation_paths(
            annotation,
            release_path,
        )
        chrom_file = self._file_service.get_assembly_file_path(
            assembly.taxa_id,
            AssemblyFileType.CHROM,
            assembly_name=assembly.name,
        )

        logger.info(
            f"Setting up Ensembl {annotation.release} for '{assembly.name}' "
            f"(organism {assembly.taxa_id})..."
        )

        try:
            self._file_service.create_annotation_release_dir(
                assembly.taxa_id,
                annotation.source,
                annotation.release,
                assembly_name=assembly.name,
            )
        except FileExistsError as exc:
            exc.add_note(
                f"Orphaned files detected: annotation '{annotation.id}' for "
                f"taxon '{taxa_id}' has files on the system but no database records"
            )
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

    def _annotate_data_in_database(
        self,
        taxa_id: int,
        dataset_id: str,
    ) -> None:
        """Add entries to DataAnnotation for a given dataset.

        :param taxa_id: NCBI taxon
        :param dataset_id: Dataset identifier
        """
        annotation = self.get_current(taxa_id)
        release_path = self.get_release_path(annotation)

        logger.debug(f"Annotating records for EUFID {dataset_id}...")

        records = list(self._data_service.get_by_dataset(dataset_id))

        features = {**self.FEATURES["conventional"], **self.FEATURES["extended"]}
        annotated_records = self._bedtools_service.annotate_data_using_ensembl(
            release_path, features, records
        )
        with InsertBuffer[DataAnnotation](self._session) as buffer:
            for record in annotated_records:
                buffer.queue(DataAnnotation(**record.model_dump()))

    def _update_database(
        self,
        annotation_id: int,
        annotation_file: Path,
    ) -> None:
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
        assembly = annotation.inst_assembly
        organism = assembly.inst_taxa.name
        filen = self.ANNOTATION_FILE(
            organism=self._ensembl_client.get_organism_url_name(organism).capitalize(),
            assembly=assembly.name,
            release=annotation.release,
            fmt=self.FMT,
        )
        # TODO: AD HOC, cf. #149
        if assembly.taxa_id in self.NO_CHR_VARIANT_TAXA:
            filen = filen.replace(".chr", "")
        url = self._ensembl_client.get_annotation_file_url(
            organism=organism,
            release=annotation.release,
            fmt=self.FMT,
            file_name=filen,
        )
        return Path(release_path, filen), url

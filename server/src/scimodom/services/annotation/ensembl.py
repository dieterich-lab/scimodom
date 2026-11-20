import logging
import shutil
from pathlib import Path
from typing import Any, ClassVar, Callable

from scimodom.database.buffer import InsertBuffer
from scimodom.database.models import Annotation, DataAnnotation, GenomicAnnotation
from scimodom.services.annotation.generic import GenericAnnotationService
from scimodom.services.ensembl import EnsemblAssemblyClient
from scimodom.utils.specs.enums import AssemblyFileType

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
    # TODO: organisms served without the ".chr" variant, cf. #149
    NO_CHR_VARIANT_TAXA: ClassVar[list[int]] = [4932, 6239]

    def __init__(self, ensembl_client: EnsemblAssemblyClient, **kwargs: Any) -> None:
        """Utility class to handle Ensembl annotation.

        :param ensembl_client: Ensembl assembly client. Owns the Ensembl
        URL layout; this service does not build URLs itself.
        :type ensembl_client: EnsemblAssemblyClient
        """
        super().__init__(**kwargs)
        self._ensembl_client = ensembl_client

    def get_annotation(self, taxa_id: int) -> Annotation:
        """Retrieve annotation from taxonomy ID.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :returns: Annotation instance
        :rtype: Annotation

        :raises: AnnotationNotFoundError
        """
        # NOTE: the annotation release used to be checked against a
        # global constant, which forced every organism into lockstep
        # with one release and is what blocked an annotation-only
        # upgrade. The annotation row is now the only statement of
        # which release an annotation is; there is nothing left for it
        # to disagree with. The release gets a database record of its
        # own, per source, in #157.
        return self.get_annotation_from_taxid_and_source(taxa_id, "ensembl")

    def create_annotation(self, taxa_id: int, **kwargs) -> None:
        """Create the current Ensembl annotation of an organism.

        This sets up the annotation that is current in the database,
        on the assembly that annotation references. It is not a way to
        install an arbitrary release: an upgrade replaces the current
        annotation and gets a method of its own, cf. #157.

        The annotation must exist in the database, and so must the
        assembly it references.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        """
        annotation = self.get_annotation(taxa_id)
        if self._release_exists(annotation.id):
            return

        assembly = annotation.inst_assembly
        release_path = self.get_release_path(annotation)
        annotation_file, url = self._get_annotation_paths(annotation, release_path)
        chrom_file = self._file_service.get_assembly_file_path(
            assembly.taxa_id, AssemblyFileType.CHROM, assembly_name=assembly.name
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

    def _annotate_data_in_database(self, taxa_id: int, dataset_id: str) -> None:
        """Annotate Data: add entries to DataAnnotation
        for a given dataset.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :param dataset_id: EUF ID
        :type dataset_id: str
        """
        annotation = self.get_annotation(taxa_id)
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
        """Construct the local path and the remote URL of an annotation file.

        Organism and assembly come from the assembly the annotation
        references, not from the components of release_path.
        """
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

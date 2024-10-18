import logging
from functools import cache

from sqlalchemy import select
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import (
    Annotation,
    RNAType,
    Modification,
)
from scimodom.services.annotation.ensembl import (
    EnsemblAnnotationService,
    AnnotationVersionError,
)
from scimodom.services.annotation.generic import (
    GenericAnnotationService,
    AnnotationNotFoundError,
)
from scimodom.services.annotation.gtrnadb import GtRNAdbAnnotationService
from scimodom.services.bedtools import get_bedtools_service
from scimodom.services.data import get_data_service
from scimodom.services.external import get_external_service
from scimodom.services.file import get_file_service
from scimodom.services.web import get_web_service
from scimodom.utils.specs.enums import AnnotationSource

logger = logging.getLogger(__name__)


RNA_TYPE_TO_ANNOTATION_SOURCE_MAP = {
    "WTS": AnnotationSource.ENSEMBL,
    "tRNA": AnnotationSource.GTRNADB,
}

# TODO, cf. #119, #149
BIOTYPES = {
    "IG_C_gene": "Ig coding",
    "IG_D_gene": "Ig coding",
    "IG_J_gene": "Ig coding",
    "IG_J_pseudogene": "Pseudogene",
    "IG_V_gene": "Ig coding",
    "IG_V_pseudogene": "Pseudogene",
    "IG_gene": "Ig coding",
    "IG_pseudogene": "Pseudogene",
    "LRG_gene": "LRG",
    "Mt_rRNA": "ncRNA",
    "Mt_tRNA": "ncRNA",
    "Mt_tRNA_pseudogene": "Pseudogene",
    "RNA-Seq_gene": "Undefined",
    "TEC": "TEC",
    "TR_gene": "TcR coding",
    "TR_pseudogene": "Pseudogene",
    "ambiguous_orf": "lncRNA",
    "cdna_update": "Undefined",
    "cDNA": "Undefined",
    "disrupted_domain": "Pseudogene",
    "EST": "Undefined",
    "lincRNA": "lncRNA",
    "miRNA": "ncRNA",
    "miRNA_pseudogene": "Pseudogene",
    "misc_RNA": "ncRNA",
    "misc_RNA_pseudogene": "Pseudogene",
    "ncRNA": "ncRNA",
    "non_coding": "lncRNA",
    "nonsense_mediated_decay": "NMD coding",
    "polymorphic_pseudogene": "Pseudogene",
    "processed_pseudogene": "Pseudogene",
    "processed_transcript": "lncRNA",
    "protein_coding": "Protein coding",
    "pseudogene": "Pseudogene",
    "rRNA": "ncRNA",
    "rRNA_pseudogene": "Pseudogene",
    "retained_intron": "lncRNA",
    "scRNA_pseudogene": "Pseudogene",
    "snRNA": "ncRNA",
    "snRNA_pseudogene": "Pseudogene",
    "snlRNA": "ncRNA",
    "snoRNA": "ncRNA",
    "snoRNA_pseudogene": "Pseudogene",
    "tRNA": "ncRNA",
    "tRNA_pseudogene": "Pseudogene",
    "transcribed_processed_pseudogene": "Pseudogene",
    "transcribed_unprocessed_pseudogene": "Pseudogene",
    "unitary_pseudogene": "Pseudogene",
    "unprocessed_pseudogene": "Pseudogene",
    "ncRNA_host": "lncRNA",
    "TR_V_pseudogene": "Pseudogene",
    "TR_V_gene": "TcR coding",
    "IG_C_pseudogene": "Pseudogene",
    "TR_C_gene": "TcR coding",
    "TR_J_gene": "TcR coding",
    "protein_coding_in_progress": "Undefined",
    "IG_M_gene": "Ig coding",
    "IG_Z_gene": "Ig coding",
    "3prime_overlapping_ncRNA": "lncRNA",
    "antisense_RNA": "lncRNA",
    "scRNA": "ncRNA",
    "RNase_MRP_RNA": "ncRNA",
    "RNase_P_RNA": "ncRNA",
    "telomerase_RNA": "ncRNA",
    "sense_intronic": "lncRNA",
    "sense_overlapping": "lncRNA",
    "TR_D_gene": "TcR coding",
    "TR_J_pseudogene": "Pseudogene",
    "ncbi_pseudogene": "Pseudogene",
    "non_stop_decay": "NSD coding",
    "pre_miRNA": "ncRNA",
    "tmRNA": "ncRNA",
    "SRP_RNA": "ncRNA",
    "ribozyme": "lncRNA",
    "ncRNA_pseudogene": "Pseudogene",
    "IG_LV_gene": "Ig coding",
    "translated_processed_pseudogene": "Pseudogene",
    "nontranslating_CDS": "Other coding",
    "translated_unprocessed_pseudogene": "Pseudogene",
    "mRNA": "Protein coding",
    "artifact": "Undefined",
    "class_I_RNA": "ncRNA",
    "class_II_RNA": "ncRNA",
    "known_ncRNA": "ncRNA",
    "transcribed_unitary_pseudogene": "Pseudogene",
    "piRNA": "ncRNA",
    "scaRNA": "ncRNA",
    "sRNA": "ncRNA",
    "antitoxin": "lncRNA",
    "macro_lncRNA": "lncRNA",
    "IG_D_pseudogene": "Pseudogene",
    "guide_RNA": "ncRNA",
    "Y_RNA": "ncRNA",
    "transposable_element": "Undefined",
    "bidirectional_promoter_lncRNA": "lncRNA",
    "unknown_likely_coding": "Other coding",
    "lncRNA": "lncRNA",
    "aligned_transcript": "Undefined",
    "antisense": "lncRNA",
    "vault_RNA": "ncRNA",
    "rnaseq_putative_cds": "Other coding",
    "transcribed_pseudogene": "Pseudogene",
    "other": "Undefined",
    "pseudogene_with_CDS": "Pseudogene",
    "misc_non_coding": "ncRNA",
    "miRNA_primary_transcript": "ncRNA",
    "protein_coding_CDS_not_defined": "lncRNA",
    "protein_coding_LoF": "LoF coding",
}


class AnnotationService:
    """Utility class to handle annotations.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param data_service: Data service instance
    :type data service: DataService
    :param bedtools_service: Bedtools service instance
    :type bedtools_service: BedToolsService
    :param external_service: External service instance
    :type external_service: ExternalService
    :param DATA_PATH: Path to data
    :type DATA_PATH: str | Path
    :param ANNOTATION_PATH: Subpath to annotation
    :type ANNOTATION_PATH: str
    :param CACHE_PATH: Path to gene cache
    :type CACHE_PATH: Path
    """

    def __init__(
        self,
        session: Session,
        services_by_annotation_source: dict[AnnotationSource, GenericAnnotationService],
    ) -> None:
        """Initializer method."""
        self._session = session
        self._services_by_annotation_source = services_by_annotation_source

    def check_annotation_source(
        self, annotation_source: AnnotationSource, modification_ids: list[int]
    ) -> bool:
        rna_types = (
            self._session.execute(
                select(RNAType.id)
                .distinct()
                .join(Modification, RNAType.modifications)
                .where(Modification.id.in_(modification_ids))
            )
            .scalars()
            .all()
        )
        if len(rna_types) > 1:
            return False
        if RNA_TYPE_TO_ANNOTATION_SOURCE_MAP[rna_types[0]] != annotation_source:
            return False
        return True

    def get_features(
        self, annotation_source: AnnotationSource
    ) -> dict[str, dict[str, str]]:
        return self._services_by_annotation_source[annotation_source].FEATURES

    def get_annotation(
        self, annotation_source: AnnotationSource, taxa_id: int
    ) -> Annotation:
        return self._services_by_annotation_source[annotation_source].get_annotation(
            taxa_id
        )

    def create_annotation(
        self, annotation_source: AnnotationSource, taxa_id: int, **kwargs
    ) -> Annotation:
        return self._services_by_annotation_source[annotation_source].create_annotation(
            taxa_id, **kwargs
        )

    def annotate_data(
        self,
        taxa_id: int,
        annotation_source: AnnotationSource,
        eufid: str,
        selection_ids: list[int],
    ):
        self._services_by_annotation_source[annotation_source].annotate_data(
            taxa_id, eufid, selection_ids
        )

    def get_features_by_rna_type(self, rna_type: str) -> list[str]:
        if rna_type not in RNA_TYPE_TO_ANNOTATION_SOURCE_MAP:
            raise NotImplementedError(
                f"The RNA type '{rna_type}' is not yet implemented."
            )
        annotation_source = RNA_TYPE_TO_ANNOTATION_SOURCE_MAP[rna_type]
        features = self.get_features(annotation_source)
        return sorted(
            [*features["conventional"].values(), *features["extended"].values()]
        )


@cache
def get_annotation_service() -> AnnotationService:
    """Helper function to set up an AnnotationService object by injecting its dependencies."""
    session = get_session()
    data_service = get_data_service()
    bedtools_service = get_bedtools_service()
    external_service = get_external_service()
    web_service = get_web_service()
    file_service = get_file_service()
    return AnnotationService(
        session=session,
        services_by_annotation_source={
            AnnotationSource.ENSEMBL: EnsemblAnnotationService(
                session=session,
                data_service=data_service,
                bedtools_service=bedtools_service,
                external_service=external_service,
                web_service=web_service,
                file_service=file_service,
            ),
            AnnotationSource.GTRNADB: GtRNAdbAnnotationService(
                session=session,
                data_service=data_service,
                bedtools_service=bedtools_service,
                external_service=external_service,
                web_service=web_service,
                file_service=file_service,
            ),
        },
    )

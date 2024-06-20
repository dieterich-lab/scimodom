import logging
import re
import shutil
from pathlib import Path
from typing import ClassVar, Callable, NamedTuple

from sqlalchemy import select

from scimodom.database.buffer import InsertBuffer
from scimodom.database.models import Annotation, Assembly, GenomicAnnotation
from scimodom.services.annotation.generic import GenericAnnotationService
import scimodom.utils.specifications as specs
from posixpath import join as urljoin

logger = logging.getLogger(__name__)


class GtRNAdbAnnotationService(GenericAnnotationService):
    """Utility class to handle GtRNAdb annotation.

    :param FMT: Annotation format. BED is used for
    annotations (GTF is no available for all organisms),
    and FASTA for coordinates mapping.
    :type FMT: list of str
    :param ANNOTATION_FILE: Annotation file pattern
    :type ANNOTATION_FILE: Callable
    :param FEATURES: Genomic features
    :type FEATURES: dict of {str: str}
    """

    FMT: ClassVar[list[str]] = ["bed", "fa"]
    ANNOTATION_FILE: ClassVar[Callable] = "{species}-tRNAs.{fmt}".format
    FEATURES: ClassVar[dict[str, dict[str, str]]] = {
        "conventional": {"exon": "Exonic"},
        "extended": {"intron": "Intronic"},
    }

    AnnotationPath: NamedTuple = NamedTuple(
        "AnnotationPath", [("annotation_file", Path), ("url", str)]
    )

    def get_annotation(self, taxa_id: int) -> Annotation:
        """Retrieve annotation from taxonomy ID.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :returns: Annotation instance
        :rtype: Annotation

        :raises: AnnotationNotFoundError
        """
        return self.get_annotation_from_taxid_and_source(taxa_id, "gtrnadb")

    def create_annotation(self, taxa_id: int, **kwargs) -> None:
        """This method automates the creation of GtRNAdb
        annotations for a given organism. The annotation
        must exists in the database.

        NOTE: Prior to calling this method, lookup the remote
        detination to find the correct domain and name, e.g.
        GTRNADB_URL/domain/name/assembly-tRNAs.fa. Choose the
        assembly that matches the current database assembly.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :param domain: Taxonomic domain e.g. eukaryota
        :type domain: str
        :param name: GtRNAdb species name (abbreviated) e.g. Mmusc39
        :type name: str
        """
        annotation = self.get_annotation(taxa_id)
        if self._release_exists(annotation.id):
            return

        domain = kwargs["domain"]
        name = kwargs["name"]
        release_path = self.get_release_path(annotation)
        annotation_paths = self._get_annotation_paths(release_path, domain, name)
        annotation_file = annotation_paths["bed"].annotation_file
        fasta_file = annotation_paths["fa"].annotation_file
        seqids = self._assembly_service.get_seqids(annotation.taxa_id)

        logger.info(
            f"Setting up GtRNAdb {annotation.release} for {annotation.taxa_id}..."
        )

        try:
            release_path.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            exc.add_note(f"... but no records found for annotation {annotation.id}.")
            raise

        try:
            for paths in annotation_paths.values():
                self._web_service.stream_request_to_file(
                    paths.url, paths.annotation_file
                )
            self._bedtools_service.gtrnadb_to_bed_features(
                annotation_file, [list(d.keys())[0] for d in self.FEATURES.values()]
            )
            # TODO
            # self._update_annotation()
            self._update_database(
                annotation_file, annotation.id, release_path.parent.parent.name
            )
            self._session.commit()
        except:
            self._session.rollback()
            shutil.rmtree(release_path)
            raise

    def _get_annotation_paths(
        self, release_path: Path, domain: str, name: str
    ) -> dict[str, AnnotationPath]:
        assembly_alt_name = self._session.execute(
            select(Assembly.alt_name).filter_by(name=release_path.parent.name)
        ).scalar_one()
        paths = {}
        for fmt in self.FMT:
            filen = self.ANNOTATION_FILE(
                assembly=assembly_alt_name,
                fmt=fmt,
            )
            url = urljoin(
                specs.GTRNADB_URL,
                domain,
                name,
                filen,
            )
            paths[fmt] = self.AnnotationPath(Path(release_path, filen), url)
        return paths

    def _patch_annotation(self, annotation_file: Path, seqids: list[str]):
        # TODO Is it general enough to handle all organisms?
        # TODO restrict to highly confident set...

        pattern = "^chr"
        repl = ""
        with open(annotation_file, "r") as fd:
            text, counter = re.subn(pattern, repl, fd.read(), flags=re.MULTILINE)

        if counter != len(text.splitlines()):
            logger.warning(
                "Chromosome substitution may have failed: expected one match per line!"
            )

        with open(annotation_file, "w") as fd:
            for line in text.splitlines():
                if line.split("\t")[0] not in seqids:
                    continue
                fd.write(f"{line}\n")

    # TODO
    def _update_annotation(self, domain, fasta_file):
        annotation_path = self.get_annotation_path()
        model_file = Path(annotation_path, domain).with_suffix(".cm").as_posix()
        sprinzl_file = Path(annotation_path, domain).with_suffix(".txt").as_posix()
        self._external_service.get_sprinzl_mapping(model_file, fasta_file, sprinzl_file)

        # self._patch_annotation(annotation_file, seqids)

        # maybe we need to patch the annotation here
        # restrict to highly confident set
        # patch
        # and at the same time update mapping file with chrom start

    def _update_database(
        self, annotation_file: Path, annotation_id: int, organism: str
    ) -> None:
        records = self._bedtools_service.get_gtrnadb_annotation_records(
            annotation_file,
            annotation_id,
            organism,
        )
        with InsertBuffer[GenomicAnnotation](self._session) as buffer:
            for record in records:
                buffer.queue(GenomicAnnotation(**record.model_dump()))

    def _annotate_data_in_database(self, taxa_id: int, eufid: str):
        pass

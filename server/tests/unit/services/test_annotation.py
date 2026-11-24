from scimodom.database.models import Annotation, AnnotationRelease
from scimodom.services.annotation import AnnotationService
from scimodom.services.annotation.generic import GenericAnnotationService
from scimodom.utils.specs.enums import AnnotationSource


class _SourceAnnotationService(GenericAnnotationService):
    """A source that serves no browsable page, cf. GtRNAdb.

    Only get_annotations is exercised here, which is defined on the
    base: this stands in for any source that does not override it.
    """

    def __init__(self, session, source: str):
        self._session = session
        self.ANNOTATION_SOURCE = source

    def _annotate_data_in_database(self, taxa_id: int, dataset_id: str):  # noqa
        pass


def _get_annotation_service(Session, sources=(AnnotationSource.ENSEMBL,)):
    session = Session()
    return AnnotationService(
        session=session,
        services_by_annotation_source={
            source: _SourceAnnotationService(session, source.value)
            for source in sources
        },
    )


# catalog


def test_get_annotations(Session, setup):  # noqa
    service = _get_annotation_service(Session)
    assert service.get_annotations() == [
        {
            "id": 1,
            "source": "ensembl",
            "release": 110,
            "archive": "jul2023",
            # the base builds no URL: that is the source's business,
            # cf. EnsemblAnnotationService.get_annotations
            "browse_url": None,
            "assembly_id": 1,
            "assembly_name": "GRCh38",
            "taxa_id": 9606,
            "taxa_name": "Homo sapiens",
        },
        {
            "id": 2,
            "source": "ensembl",
            "release": 110,
            "archive": "jul2023",
            "browse_url": None,
            "assembly_id": 2,
            "assembly_name": "GRCm38",
            "taxa_id": 10090,
            "taxa_name": "Mus musculus",
        },
    ]


def test_get_annotations_by_taxa(Session, setup):  # noqa
    service = _get_annotation_service(Session)
    assert [row["taxa_id"] for row in service.get_annotations(10090)] == [10090]


def test_get_annotations_spans_every_source(Session, setup):  # noqa
    # each source answers for itself; the facade merges and orders
    service = _get_annotation_service(
        Session, (AnnotationSource.ENSEMBL, AnnotationSource.GTRNADB)
    )
    session = service._session
    session.add(AnnotationRelease(source="gtrnadb", release=19, archive=None))
    session.add(
        Annotation(release=19, assembly_id=1, source="gtrnadb", version="EyRBnPeVwbzW")
    )
    session.commit()

    assert [(row["taxa_id"], row["source"]) for row in service.get_annotations()] == [
        (9606, "ensembl"),
        (9606, "gtrnadb"),
        (10090, "ensembl"),
    ]


def test_get_annotations_source_without_archive(Session, setup):  # noqa
    # a source that keeps no per-release archive, cf. GtRNAdb
    service = _get_annotation_service(Session, (AnnotationSource.GTRNADB,))
    session = service._session
    session.add(AnnotationRelease(source="gtrnadb", release=19, archive=None))
    session.add(
        Annotation(release=19, assembly_id=1, source="gtrnadb", version="EyRBnPeVwbzW")
    )
    session.commit()

    row = service.get_annotations()[0]
    assert row["archive"] is None
    assert row["browse_url"] is None


def test_get_annotations_empty_source(Session, setup):  # noqa
    service = _get_annotation_service(Session, (AnnotationSource.GTRNADB,))
    assert service.get_annotations() == []

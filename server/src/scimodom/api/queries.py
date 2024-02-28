import os
from pathlib import Path

from flask import request
from flask_cors import cross_origin
from sqlalchemy import select, func

from . import api
from scimodom.database.database import get_session
from scimodom.database.models import (
    Annotation,
    Assembly,
    Association,
    Data,
    DataAnnotation,
    Dataset,
    DetectionMethod,
    DetectionTechnology,
    GenomicAnnotation,
    Modification,
    Modomics,
    Organism,
    Project,
    ProjectSource,
    Taxonomy,
    Taxa,
    Selection,
)
import scimodom.database.queries as queries
from scimodom.services.importer import BEDImporter
from scimodom.services.annotation import AnnotationService
from scimodom.services.assembly import AssemblyService
from scimodom.utils.models import records_factory
from scimodom.utils.operations import get_op
import scimodom.utils.specifications as specs

FEATURES = list(
    {
        **AnnotationService.FEATURES["conventional"],
        **AnnotationService.FEATURES["extended"],
    }.values()
)
BIOTYPES = specs.BIOTYPES
MAPPED_BIOTYPES = sorted(list(set(BIOTYPES.values())))


@api.route("/selection", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_selection():
    """Get available selection =
    (modification, organism, technology)."""
    query = (
        select(
            Modification.id.label("modification_id"),
            Modification.rna,
            Modomics.short_name.label("modomics_sname"),
            DetectionTechnology.id.label("technology_id"),
            DetectionMethod.cls,
            DetectionMethod.meth,
            DetectionTechnology.tech,
            Organism.id.label("organism_id"),
            Taxonomy.domain,
            Taxonomy.kingdom,
            Taxa.id.label("taxa_id"),
            Taxa.short_name.label("taxa_sname"),
            Organism.cto,
            Selection.id.label("selection_id"),
        )
        .join_from(
            Selection,
            Modification,
            Selection.inst_modification,
        )
        .join_from(
            Selection,
            DetectionTechnology,
            Selection.inst_technology,
        )
        .join_from(Selection, Organism, Selection.inst_organism)
        .join_from(Modification, Modomics, Modification.inst_modomics)
        .join_from(
            DetectionTechnology,
            DetectionMethod,
            DetectionTechnology.inst_method,
        )
        .join_from(Organism, Taxa, Organism.inst_taxa)
        .join_from(Taxa, Taxonomy, Taxa.inst_taxonomy)
    )

    return _dump(query)


@api.route("/chrom/<taxid>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_chrom(taxid):
    """Provides access to chrom.sizes for one
    selected organism for current database version."""
    query = queries.get_assembly_version()
    version = get_session().execute(query).scalar_one()

    query = queries.query_column_where(
        Assembly, ["name", "id"], filters={"taxa_id": taxid, "version": version}
    )
    assembly_name, assembly_id = get_session().execute(query).all()[0]
    query = queries.query_column_where(Taxa, "name", filters={"id": taxid})
    organism_name = get_session().execute(query).scalar_one()
    assembly_service = AssemblyService.from_id(get_session(), assembly_id=assembly_id)
    parent, filen = assembly_service.get_chrom_path(organism_name, assembly_name)
    chrom_file = Path(parent, filen)

    chroms = []
    with open(chrom_file, "r") as fh:
        for line in fh:
            chrom, size = line.strip().split(None, 1)
            chroms.append({"chrom": chrom, "size": int(size.strip())})

    return chroms


@api.route("/search", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_search():
    """Get Data records for conditional selection, add
    filters and sort."""
    selection_ids = request.args.getlist("selection", type=int)
    taxa_id = request.args.get("taxid", type=int)
    chrom = request.args.get("chrom", type=str)
    chrom_start = request.args.get("chromStart", type=int)
    chrom_end = request.args.get("chromEnd", type=int)
    first_record = request.args.get("firstRecord", type=int)
    max_records = request.args.get("maxRecords", type=int)
    multi_sort = request.args.getlist("multiSort", type=str)
    table_filter = request.args.getlist("tableFilter", type=str)

    # base query
    query = (
        select(
            Data.id,
            Data.chrom,
            Data.start,
            Data.end,
            Data.name,
            Data.score,
            Data.strand,
            Data.coverage,
            Data.frequency,
            func.group_concat(DataAnnotation.feature.distinct()).label("feature"),
            func.group_concat(GenomicAnnotation.biotype.distinct()).label(
                "gene_biotype"
            ),
            func.group_concat(GenomicAnnotation.name.distinct()).label("gene_name"),
            DetectionTechnology.tech,
            Association.dataset_id,
        )
        .join_from(DataAnnotation, Data, DataAnnotation.inst_data)
        .join_from(DataAnnotation, GenomicAnnotation, DataAnnotation.inst_genomic)
        .join_from(Data, Association, Data.inst_association)
        .join_from(Association, Selection, Association.inst_selection)
        .join_from(Selection, DetectionTechnology, Selection.inst_technology)
        .where(Association.selection_id.in_(selection_ids))
    )

    # coordinate filter
    if chrom:
        query = (
            query.where(Data.chrom == chrom)
            .where(Data.start >= chrom_start)
            .where(Data.end < chrom_end)
        )

    # annotation filter
    feature_flt = next((flt for flt in table_filter if "feature" in flt), None)
    if feature_flt:
        _, features, _ = _get_flt(feature_flt)
        query = query.where(DataAnnotation.feature.in_(features))

    version_query = queries.get_annotation_version()
    version = get_session().execute(version_query).scalar_one()
    annotation_query = queries.query_column_where(
        Annotation,
        "id",
        filters={"taxa_id": taxa_id, "version": version},
    )
    annotation = get_session().execute(annotation_query).scalar_one()

    # index speed up on annotation_id + biotypes + name
    biotype_flt = next((flt for flt in table_filter if "gene_biotype" in flt), None)
    if biotype_flt:
        _, mapped_biotypes, _ = _get_flt(biotype_flt)
        biotypes = [k for k, v in BIOTYPES.items() if v in mapped_biotypes]
    else:
        biotypes = BIOTYPES.keys()
    query = query.where(GenomicAnnotation.annotation_id == annotation).where(
        GenomicAnnotation.biotype.in_(biotypes)
    )
    name_flt = next((flt for flt in table_filter if "gene_name" in flt), None)
    if name_flt:
        _, name, _ = _get_flt(name_flt)
        query = query.where(GenomicAnnotation.name.ilike(f"{name[0]}%"))

    query = query.group_by(DataAnnotation.data_id)

    # get length
    length = get_session().scalar(
        select(func.count()).select_from(query.with_only_columns(Data.id))
    )

    # sort filter
    # index speed up for chrom + start
    if not multi_sort:
        chrom_expr = _get_arg_sort("chrom%2Basc")
        start_expr = _get_arg_sort("start%2Basc")
        query = query.order_by(eval(chrom_expr), eval(start_expr))
    else:
        for flt in multi_sort:
            expr = _get_arg_sort(flt)
            query = query.order_by(eval(expr))

    # paginate
    query = query.offset(first_record).limit(max_records)

    response_object = dict()
    response_object["totalRecords"] = length
    response_object["records"] = _dump(query)
    response_object["features"] = FEATURES
    response_object["biotypes"] = MAPPED_BIOTYPES

    return response_object


@api.route("/browse", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_dataset():
    """Retrieve all dataset/projects."""

    # 11.2023 no lazy loading, all data is returned
    # filtering is done in Vue.js

    query = (
        select(
            Dataset.project_id,
            Dataset.id.label("dataset_id"),
            Dataset.title.label("dataset_title"),
            Dataset.sequencing_platform,
            Dataset.basecalling,
            Dataset.bioinformatics_workflow,
            Dataset.experiment,
            Project.title.label("project_title"),
            Project.summary.label("project_summary"),
            Project.date_published,
            Project.date_added,
            func.group_concat(ProjectSource.doi.distinct()).label("doi"),
            func.group_concat(ProjectSource.pmid.distinct()).label("pmid"),
            Modification.rna,
            func.group_concat(Modomics.short_name.distinct()).label("modomics_sname"),
            DetectionTechnology.tech,
            Taxa.short_name.label("taxa_sname"),
            Organism.cto,
        )
        .join_from(
            Dataset,
            Project,
            Dataset.project_id == Project.id,
        )
        .join_from(
            Project, ProjectSource, Project.id == ProjectSource.project_id, isouter=True
        )
        .join_from(Dataset, Association, Dataset.id == Association.dataset_id)
        .join_from(Association, Selection, Association.selection_id == Selection.id)
        .join_from(
            Selection, Modification, Selection.modification_id == Modification.id
        )
        .join_from(
            Selection,
            DetectionTechnology,
            Selection.technology_id == DetectionTechnology.id,
        )
        .join_from(Selection, Organism, Selection.organism_id == Organism.id)
        .join_from(Modification, Modomics, Modification.modomics_id == Modomics.id)
        .join_from(Organism, Taxa, Organism.taxa_id == Taxa.id)
        .group_by(Dataset.project_id, Dataset.id)
    )

    return _dump(query)


@api.route("/compare/<step>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_comparison(step):
    """Retrieve ..."""

    # API call in compare, then pass as params to SPA components
    # but sending all datasets may be too large?
    # final call after dataset selection + query
    # + lazy loading of results?

    if step == "dataset":
        query = (
            select(
                Dataset.id.label("dataset_id"),
                Dataset.title.label("dataset_title"),
                Modification.id.label("modification_id"),
                DetectionTechnology.id.label("technology_id"),
                Organism.id.label("organism_id"),
            )
            .join_from(Dataset, Association, Dataset.id == Association.dataset_id)
            .join_from(Association, Selection, Association.selection_id == Selection.id)
            .join_from(
                Selection, Modification, Selection.modification_id == Modification.id
            )
            .join_from(
                Selection,
                DetectionTechnology,
                Selection.technology_id == DetectionTechnology.id,
            )
            .join_from(Selection, Organism, Selection.organism_id == Organism.id)
        )

        records = _dump(query)

    # query = (
    # select(Taxa.short_name.distinct(), Taxonomy.kingdom)
    # .join_from(Taxa, Taxonomy, Taxa.taxonomy_id == Taxonomy.id)
    # .join_from(Taxa, Organism, Taxa.id == Organism.taxa_id)
    # )

    ## so far no order
    ## [('H. sapiens', 'Animalia'), ('M. musculus', 'Animalia')]
    ## we need to reformat to fit the "grouped dropdown component"
    ## we also probably need to add ids to retrieve the final selection
    ## i.e. taxa, modification, and technology ids
    ## same below

    # query = select(
    # Modification.rna.distinct(),
    # Modomics.short_name,
    # ).join_from(Modification, Modomics, Modification.modomics_id == Modomics.id)

    ## [('mRNA', 'm6A'), ('mRNA', 'm5C'), ('rRNA', 'm6A'), ('mRNA', 'Y'), ('tRNA', 'Y')]

    # query = select(DetectionMethod.meth.distinct(), DetectionTechnology.tech).join_from(
    # DetectionMethod,
    # DetectionTechnology,
    # DetectionMethod.id == DetectionTechnology.method_id,
    # )

    ## [('Chemical-assisted sequencing', 'm6A-SAC-seq'), ('Native RNA sequencing', 'Nanopore'), ('Chemical-assisted sequencing', 'GLORI'), ('Enzyme/protein-assisted sequencing', 'm5C-miCLIP'), ('Enzyme/protein-assisted sequencing', 'm6ACE-seq'), ('Chemical-assisted sequencing', 'BID-seq'), ('Antibody-based sequencing', 'm6A-seq/MeRIP'), ('Enzyme/protein-assisted sequencing', 'eTAM-seq')]

    elif step == "ops":
        dataset_ids_a = request.args.getlist("datasetIdsA", type=str)
        dataset_ids_b = request.args.getlist("datasetIdsB", type=str)
        dataset_upload = request.args.get("datasetUpload", type=str)
        query_operation = request.args.get("queryOperation", type=str)

        query = (
            select(
                Data.chrom,
                Data.start,
                Data.end,
                Data.name,
                Data.score,
                Data.strand,
                Association.dataset_id,
                # Data.dataset_id,
                Data.coverage,
                Data.frequency,
            )
            .join_from(Data, Association, Data.inst_association)
            .where(Association.dataset_id.in_(dataset_ids_a))
            # .order_by(Data.chrom.asc(), Data.start.asc())
        )
        a_records = get_session().execute(query).all()

        # AD HOC - EUF VERSION SHOULD COME FROM SOMEWHERE ELSE!
        if dataset_upload:
            filen = Path(dataset_upload).stem
            b_records = [
                BEDImporter(
                    filen, open(dataset_upload, "r"), filen, "1.7"
                ).get_records()
            ]
        else:
            b_records = []
            for idx in dataset_ids_b:
                query = (
                    select(
                        Data.chrom,
                        Data.start,
                        Data.end,
                        Data.name,
                        Data.score,
                        Data.strand,
                        Association.dataset_id,
                        # Data.dataset_id,
                        Data.coverage,
                        Data.frequency,
                    )
                    .join_from(Data, Association, Data.inst_association)
                    .where(Association.dataset_id == idx)
                    # .where(Data.dataset_id == idx)
                )
                b_records.append(get_session().execute(query).all())

        op, strand = query_operation.split("S")
        c_records = get_op(op)(a_records, b_records, s=eval(strand))
        records = [records_factory(op.capitalize(), r)._asdict() for r in c_records]

    return records


@api.route("/upload", methods=["POST"])
@cross_origin(supports_credentials=True)
def upload_file():
    """Upload ..."""

    # TODO: define app.config['UPLOAD_PATH'] = UPLOAD_FOLDER
    # ALLOWED_EXTENSIONS are dealt with PrimeVue FileUpload
    # PEP8 import
    from werkzeug.utils import secure_filename

    upload = os.getenv("UPLOAD_PATH")
    if "file" not in request.files:
        # this shouldn't happen, but ...
        pass
    # or empty file without a filename should not happen
    rfile = request.files["file"]
    filename = secure_filename(rfile.filename)
    response = Path(upload, filename)
    rfile.save(response)

    return response.as_posix()


def _dump(query):
    return [r._asdict() for r in get_session().execute(query)]


def _get_arg_sort(string: str, url_split: str = "%2B") -> str:
    """Format Data table sort.

    :param string: Formatted sort string
    :type string: str
    :param url_split: Separator
    :type url_split: str
    :returns: Query string
    :rtype: str
    """
    col, order = string.split(url_split)
    return f"Data.{col}.{order}()"


def _get_flt(string, url_split="%2B") -> tuple[str, list[str], str]:
    """Retrieve generic filters. The operator
    can be used as a key, and may not
    necessarily match an SQLAlchemy operator.

    :param string: Formatted filter string
    :type string: str
    :param url_split: Separator
    :type url_split: str
    :returns: Tuple of (column, list of values, operator)
    :rtype: tuple
    """
    col, val, operator = string.split(url_split)
    return col, val.split(","), operator

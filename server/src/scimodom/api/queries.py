import os
import json

import scimodom.utils.specifications as specs

# import scimodom.database.queries as queries

from pathlib import Path
from flask import request
from flask_cors import cross_origin
from sqlalchemy import select, func, and_, or_, not_

from . import api
from scimodom.database.database import get_session
from scimodom.database.models import (
    Modomics,
    Modification,
    DetectionMethod,
    DetectionTechnology,
    Data,
    Dataset,
    Project,
    ProjectSource,
    Taxonomy,
    Taxa,
    Organism,
    Association,
    Selection,
    GenomicAnnotation,
)


prop_comparators = {
    "startsWith": "istartswith",
    "contains": "icontains",
    "notContains": "icontains",
    "endsWith": "iendswith",
    "equals": "__eq__",
    "notEquals": "__eq__",
    "in": "in_",
}


def _dump(query):
    return [r._asdict() for r in get_session().execute(query)]


def _paginate(query, first, rows):
    length = get_session().scalar(select(func.count()).select_from(query))
    query = query.offset(first).limit(rows)
    return (length, query)


def _get_arg_sort(string, url_split="%2B"):
    col, order = string.split(url_split)
    return f"Data.{col}.{order}()"


def _get_arg_flt(string, url_split="%2B", substr="_gc"):
    col, val, operator = string.split(url_split)
    col = col.replace(substr, "")
    arg = (
        [k for k, v in specs.BIOTYPES.items() if v in val.split(",")]
        if "biotype" in col
        else val.split(",")
        if "feature" in col
        else val
    )
    arg_str = f"({arg})" if operator == "in" else f"('{arg}')"
    expr = f"GenomicAnnotation.{col}.{prop_comparators[operator]}{arg_str}"
    if operator.startswith("not"):
        expr = f"~{expr}"
    return expr


@api.route("/selection", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_selection():
    """Retrieve all available selections."""

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
            Taxonomy.phylum,
            Taxa.short_name.label("taxa_sname"),
            Organism.cto,
        )
        .join_from(
            Selection,
            Modification,
            Selection.modification_id == Modification.id,
        )
        .join_from(
            Selection,
            DetectionTechnology,
            Selection.technology_id == DetectionTechnology.id,
        )
        .join_from(Selection, Organism, Selection.organism_id == Organism.id)
        .join_from(Modification, Modomics, Modification.modomics_id == Modomics.id)
        .join_from(
            DetectionTechnology,
            DetectionMethod,
            DetectionTechnology.method_id == DetectionMethod.id,
        )
        .join_from(Organism, Taxa, Organism.taxa_id == Taxa.id)
        .join_from(Taxa, Taxonomy, Taxa.taxonomy_id == Taxonomy.id)
    )

    return _dump(query)


@api.route("/search", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_search():
    """Retrieve conditional selections."""
    modification_ids = request.args.getlist("modification", type=int)
    technology_ids = request.args.getlist("technology", type=int)
    organism_ids = request.args.getlist("organism", type=int)
    first_record = request.args.get("firstRecord", type=int)
    max_records = request.args.get("maxRecords", type=int)
    multi_sort = request.args.getlist("multiSort", type=str)
    table_filter = request.args.getlist("tableFilter", type=str)

    print(f"FILTERS: {table_filter}")
    print(f"SORT: {multi_sort}")

    query = (
        select(
            Data.chrom,
            Data.start,
            Data.end,
            Data.name,
            Data.score,
            Data.strand,
            Data.coverage,
            Data.frequency,
            func.group_concat(GenomicAnnotation.gene_name.distinct()).label(
                "gene_name_gc"
            ),
            func.group_concat(GenomicAnnotation.gene_id.distinct()).label("gene_id_gc"),
            func.group_concat(GenomicAnnotation.gene_biotype.distinct()).label(
                "gene_biotype_gc"
            ),
            func.group_concat(GenomicAnnotation.feature.distinct()).label("feature_gc"),
        )
        .join_from(Association, Data, Association.dataset_id == Data.dataset_id)
        .join_from(Association, Selection, Association.selection_id == Selection.id)
        .join_from(Data, GenomicAnnotation, Data.id == GenomicAnnotation.data_id)
        .group_by(Data.id)
    )
    # an empty list would return an empty set...
    if modification_ids:
        query = query.where(Selection.modification_id.in_(modification_ids))
    if technology_ids:
        query = query.where(Selection.technology_id.in_(technology_ids))
    if organism_ids:
        query = query.where(Selection.organism_id.in_(organism_ids))

    feature_query = select(GenomicAnnotation.feature.distinct()).where(
        GenomicAnnotation.data_id.in_(query.with_only_columns(Data.id))
    )
    features = get_session().execute(feature_query).scalars().all()
    biotype_query = select(GenomicAnnotation.gene_biotype.distinct()).where(
        GenomicAnnotation.data_id.in_(query.with_only_columns(Data.id))
    )
    biotypes = get_session().execute(biotype_query).scalars().all()
    biotypes = sorted(
        list(
            set(
                [specs.BIOTYPES[biotype] for biotype in biotypes if biotype is not None]
            )
        )
    )

    # removes duplicates from INNER JOIN Association/Selection (and GenomicAnnotation feature?)
    # but check https://github.com/dieterich-lab/scimodom/issues/53
    query = query.distinct()

    for sort in multi_sort:
        expr = _get_arg_sort(sort)
        query = query.order_by(eval(expr))

    # order of sort and filter????
    for flt in table_filter:
        expr = _get_arg_flt(flt)
        query = query.where(eval(expr))

    response_object = dict()
    response_object["features"] = features
    response_object["biotypes"] = biotypes
    response_object["totalRecords"], query = _paginate(query, first_record, max_records)
    response_object["records"] = _dump(query)

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
            func.group_concat(ProjectSource.doi.distinct()),
            func.group_concat(ProjectSource.pmid.distinct()),
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

    from scimodom.services.importer import BEDImporter
    from scimodom.utils.operations import get_op
    from scimodom.utils.models import records_factory

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
                Data.dataset_id,
                Data.coverage,
                Data.frequency,
            ).where(Data.dataset_id.in_(dataset_ids_a))
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
                query = select(
                    Data.chrom,
                    Data.start,
                    Data.end,
                    Data.name,
                    Data.score,
                    Data.strand,
                    Data.dataset_id,
                    Data.coverage,
                    Data.frequency,
                ).where(Data.dataset_id == idx)
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

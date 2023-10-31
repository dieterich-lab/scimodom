import json
from sqlalchemy import select, func
from flask import request
from flask_cors import cross_origin

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
)
from scimodom.database.database import get_session

# import scimodom.database.queries as queries

from . import api


def convert_tup_list_to_json(keys, query_list):
    # quickly convert to dict/json
    # we need a true solution to jsonify the query results...
    return [dict(zip(keys, q)) for q in query_list]


def paginate(query, first, rows):
    length = get_session().scalar(select(func.count()).select_from(query))
    query = query.offset(first).limit(rows)
    return (length, query)


@api.route("/selection", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_selection():
    """Retrieve all available selections."""

    keys = [
        "modification_id",
        "rna",
        "modomics_sname",
        "technology_id",
        "cls",
        "meth",
        "tech",
        "organism_id",
        "domain",
        "kingdom",
        "phylum",
        "taxa_sname",
        "cto",
    ]

    query = (
        select(
            Modification.id,
            Modification.rna,
            Modomics.short_name,
            DetectionTechnology.id,
            DetectionMethod.cls,
            DetectionMethod.meth,
            DetectionTechnology.tech,
            Organism.id,
            Taxonomy.domain,
            Taxonomy.kingdom,
            Taxonomy.phylum,
            Taxa.short_name,
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

    selections = get_session().execute(query).all()
    return convert_tup_list_to_json(keys, selections)


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

    keys = [
        "chrom",
        "start",
        "end",
        "name",
        "score",
        "strand",
        "coverage",
        "frequency",
        "ref_base",
    ]

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
            Data.ref_base,
        )
        .join_from(Association, Data, Association.dataset_id == Data.dataset_id)
        .join_from(Association, Selection, Association.selection_id == Selection.id)
    )
    # an empty list would return an empty set...
    if modification_ids:
        query = query.where(Selection.modification_id.in_(modification_ids))
    if technology_ids:
        query = query.where(Selection.technology_id.in_(technology_ids))
    if organism_ids:
        query = query.where(Selection.organism_id.in_(organism_ids))
    for sort in multi_sort:
        col, order = sort.split(".")
        expr = eval(f"Data.{col}.{order}()")
        query = query.order_by(expr)

    # TODO: so far this hasn't hit the DB
    # TODO: caching (how/when?)

    response_object = dict()
    response_object["totalRecords"], query = paginate(query, first_record, max_records)
    records = get_session().execute(query).all()
    response_object["records"] = convert_tup_list_to_json(keys, records)

    return response_object


@api.route("/browse", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_dataset():
    """Retrieve all dataset/projects."""

    # 11.2023 no lazy loading, all data is returned
    # filtering is done in Vue.js

    keys = [
        "project_id",
        "dataset_id",
        "dataset_title",
        "sequencing_platform",
        "basecalling",
        "bioinformatics_workflow",
        "experiment",
        "project_title",
        "project_summary",
        "date_published",
        "date_added",
        "doi",
        "pmid",
        "rna",
        "modomics_sname",
        "tech",
        "taxa_sname",
        "cto",
    ]

    query = (
        select(
            Dataset.project_id,
            Dataset.id,
            Dataset.title,
            Dataset.sequencing_platform,
            Dataset.basecalling,
            Dataset.bioinformatics_workflow,
            Dataset.experiment,
            Project.title,
            Project.summary,
            Project.date_published,
            Project.date_added,
            func.group_concat(ProjectSource.doi.distinct()),
            func.group_concat(ProjectSource.pmid.distinct()),
            Modification.rna,
            Modomics.short_name,
            DetectionTechnology.tech,
            Taxa.short_name,
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

    dataset = get_session().execute(query).all()
    return convert_tup_list_to_json(keys, dataset)


@api.route("/modification/<string:mod>")
@cross_origin(supports_credentials=True)
def get_mod(mod):
    values = (
        get_session()
        .execute(select(Modomics).where(Modomics.short_name == mod))
        .first()
    )
    results = [{"id": value.id, "name": value.name} for value in values]

    # http://127.0.0.1:5000/api/v0/modification/m6A
    return (json.dumps(results), 200, {"content_type": "application/json"})


# @api.route("/search")
# @cross_origin(supports_credentials=True)
# def get_search():
## this is a quick prototyping for a typical search query (Search view)
## http://127.0.0.1:5000/api/v0/search?modification=m6A-mRNA&technology=m6A-SAC-seq&organism=9606&cto=HEK293
## we don't know yet what we get: ids? or some other column e.g. short_name?
## in some cases, e.g. modification and rna type, or organism and cto, we don't want to
## assume any order/matching
## and maybe we need a fall-back if missing arguments, e.g. all technologies
## (coming from the FE, this won't happen, but we want the API to work in general)
## also we need to jsonify the output, etc.

# modification = request.args.getlist("modification")
# technology = request.args.getlist("technology")
# organism = request.args.getlist("organism")
# cto = request.args.getlist("cto")

# mods = [m.split("-")[0] for m in modification]
# rna_types = [m.split("-")[1] for m in modification]

# query = select(Modomics.id).where(Modomics.short_name.in_(mods))
# modomics_ids = get_session().execute(query).scalars().all()
# modification_ids = []
# for midx, ridx in zip(modomics_ids, rna_types):
# query = select(Modification.id).where(
# Modification.modomics_id == midx, Modification.rna == ridx
# )
# idx = get_session().execute(query).scalar()
# modification_ids.append(idx)

# organism_ids = []
# for o, c in zip(organism, cto):
# query = select(Organism.id).where(Organism.cto == c, Organism.taxa_id == o)
# idx = get_session().execute(query).scalar()
# organism_ids.append(idx)

# query = (
# select(
# Data.chrom,
# Data.start,
# Data.end,
# Data.name,
# Data.score,
# Data.strand,
# Data.coverage,
# Data.frequency,
# DetectionTechnology.tech,
# Taxa.short_name,
# Organism.cto,
# )
# .join_from(
# Association,
# Data,
# Association.dataset_id == Data.dataset_id,
# )
# .join_from(
# Association,
# Selection,
# Association.selection_id == Selection.id,
# )
# .join_from(
# Selection, Modification, Selection.modification_id == Modification.id
# )
# .join_from(
# Selection,
# DetectionTechnology,
# Selection.technology_id == DetectionTechnology.id,
# )
# .join_from(Selection, Organism, Selection.organism_id == Organism.id)
# .join_from(Organism, Taxa, Organism.taxa_id == Taxa.id)
# .where(
# Modification.id.in_(modification_ids),
# DetectionTechnology.tech.in_(technology),
# Organism.id.in_(organism_ids),
# )
# )

# records = get_session().execute(query).all()

# results = [
# {
# "chrom": r[0],
# "start": r[1],
# "end": r[2],
# "name": r[3],
# "score": r[4],
# "strand": r[5],
# "coverage": r[6],
# "frequency": r[7],
# "tech": r[8],
# "short_name": r[9],
# "cto": r[10],
# }
# for r in records
# ]

# return (json.dumps(results), 200, {"content_type": "application/json"})

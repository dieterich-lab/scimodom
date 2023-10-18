import json
from sqlalchemy import select
from flask import request
from flask_cors import cross_origin

from scimodom.database.models import (
    Modomics,
    Modification,
    DetectionTechnology,
    Data,
    Taxa,
    Organism,
    Association,
    Selection,
)
from scimodom.database.database import get_session

# import scimodom.database.queries as queries

from . import api


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


@api.route("/search")
@cross_origin(supports_credentials=True)
def get_search():
    # this is a quick prototyping for a typical search query (Search view)
    # http://127.0.0.1:5000/api/v0/search?modification=m6A-mRNA&technology=m6A-SAC-seq&organism=9606&cto=HEK293
    # we don't know yet what we get: ids? or some other column e.g. short_name?
    # in some cases, e.g. modification and rna type, or organism and cto, we don't want to
    # assume any order/matching
    # and maybe we need a fall-back if missing arguments, e.g. all technologies
    # (coming from the FE, this won't happen, but we want the API to work in general)
    # also we need to jsonify the output, etc.

    modification = request.args.getlist("modification")
    technology = request.args.getlist("technology")
    organism = request.args.getlist("organism")
    cto = request.args.getlist("cto")

    mods = [m.split("-")[0] for m in modification]
    rna_types = [m.split("-")[1] for m in modification]

    query = select(Modomics.id).where(Modomics.short_name.in_(mods))
    modomics_ids = get_session().execute(query).scalars().all()
    modification_ids = []
    for midx, ridx in zip(modomics_ids, rna_types):
        query = select(Modification.id).where(
            Modification.modomics_id == midx, Modification.rna == ridx
        )
        idx = get_session().execute(query).scalar()
        modification_ids.append(idx)

    organism_ids = []
    for o, c in zip(organism, cto):
        query = select(Organism.id).where(Organism.cto == c, Organism.taxa_id == o)
        idx = get_session().execute(query).scalar()
        organism_ids.append(idx)

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
            DetectionTechnology.tech,
            Taxa.short_name,
            Organism.cto,
        )
        .join_from(
            Association,
            Data,
            Association.dataset_id == Data.dataset_id,
        )
        .join_from(
            Association,
            Selection,
            Association.selection_id == Selection.id,
        )
        .join_from(
            Selection, Modification, Selection.modification_id == Modification.id
        )
        .join_from(
            Selection,
            DetectionTechnology,
            Selection.technology_id == DetectionTechnology.id,
        )
        .join_from(Selection, Organism, Selection.organism_id == Organism.id)
        .join_from(Organism, Taxa, Organism.taxa_id == Taxa.id)
        .where(
            Modification.id.in_(modification_ids),
            DetectionTechnology.tech.in_(technology),
            Organism.id.in_(organism_ids),
        )
    )

    records = get_session().execute(query).all()

    results = [
        {
            "chrom": r[0],
            "start": r[1],
            "end": r[2],
            "name": r[3],
            "score": r[4],
            "strand": r[5],
            "coverage": r[6],
            "frequency": r[7],
            "tech": r[8],
            "short_name": r[9],
            "cto": r[10],
        }
        for r in records
    ]

    return (json.dumps(results), 200, {"content_type": "application/json"})
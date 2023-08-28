# template queries

from scimodom.database.models import Modification, DetectionTechnology, Organism, Selection, Assembly

from sqlalchemy import select

# simple row queries for id

def modification(rna, modomics_id):
    query = (
        select(Modification.id).where(
            Modification.rna == rna, 
            Modification.modomics_id == modomics_id
        )
    )
    return query


def technology(tech, method_id):
    query = (
        select(DetectionTechnology.id).where(
            DetectionTechnology.tech == tech, 
            DetectionTechnology.method_id == method_id
        )
    )
    return query


def organism(cto, taxa_id):
    query = (
        select(Organism.id).where(
            Organism.cto == cto, 
            Organism.taxa_id == taxa_id
        )
    )
    return query


def assembly(name, taxa_id):
    query = (
        select(Assembly.id).where(
            Assembly.name == name, 
            Assembly.taxa_id == taxa_id
        )
    )
    return query


def selection(modification_id, technology_id, organism_id):
    query = (
        select(Selection.id).where(
            Selection.modification_id == modification_id, 
            Selection.technology_id == technology_id,
            Selection.organism_id == organism_id
        )
    )
    return query






# template queries

from scimodom.database.models import (
    Modification,
    DetectionTechnology,
    Taxa,
    Organism,
    Selection,
    Assembly,
    AssemblyVersion,
    Project,
    ProjectContact,
    Dataset,
    Data,
)

from sqlalchemy import select

# special queries


def get_assembly_version():
    return select(AssemblyVersion.version_num)


# simple row queries for id


# TODO: generalise the simple one element queries
# input dict column_name: value
#


def taxa(target, filters=dict()):
    query = select(getattr(Taxa, target))
    for name, value in filters.items():
        query = query.where(getattr(Taxa, name) == value)
    return query


def assembly_(target, filters=dict()):
    query = select(getattr(Assembly, target))
    for name, value in filters.items():
        query = query.where(getattr(Assembly, name) == value)
    return query


def modification(rna, modomics_id):
    query = select(Modification.id).where(
        Modification.rna == rna, Modification.modomics_id == modomics_id
    )
    return query


def technology(tech, method_id):
    query = select(DetectionTechnology.id).where(
        DetectionTechnology.tech == tech, DetectionTechnology.method_id == method_id
    )
    return query


def organism(cto, taxa_id):
    query = select(Organism.id).where(Organism.cto == cto, Organism.taxa_id == taxa_id)
    return query


def assembly(name, taxa_id):
    query = select(Assembly.id).where(
        Assembly.name == name, Assembly.taxa_id == taxa_id
    )
    return query


def selection(modification_id, technology_id, organism_id):
    query = select(Selection.id).where(
        Selection.modification_id == modification_id,
        Selection.technology_id == technology_id,
        Selection.organism_id == organism_id,
    )
    return query


def contact(name, institution, email):
    query = select(ProjectContact.id).where(
        ProjectContact.contact_name == name,
        ProjectContact.contact_institution == institution,
        ProjectContact.contact_email == email,
    )
    return query


def dataset(target, filters=dict()):
    query = select(getattr(Taxa, target))
    for name, value in filters.items():
        query = query.where(getattr(Taxa, name) == value)
    return query


# def taxa(target, filters=dict()):
# query = select(getattr(Taxa, target))
# for name, value in filters.items():
# query = query.where(getattr(Taxa, name) == value)
# return query


# def assembly(target, filters=dict()):
# query = select(getattr(Assembly, target))
# for name, value in filters.items():
# query = query.where(getattr(Assembly, name) == value)
# return query


# def modification(target, filters=dict()):
# query = select(getattr(Modification, target))
# for name, value in filters.items():
# query = query.where(getattr(Modification, name) == value)
# return query


# def technology(target, filters=dict()):
# query = select(getattr(DetectionTechnology, target))
# for name, value in filters.items():
# query = query.where(getattr(DetectionTechnology, name) == value)
# return query


# def organism(target, filters=dict()):
# query = select(getattr(Organism, target))
# for name, value in filters.items():
# query = query.where(getattr(Organism, name) == value)
# return query


# def selection(target, filters=dict()):
# query = select(getattr(Selection, target))
# for name, value in filters.items():
# query = query.where(getattr(Selection, name) == value)
# return query

# def contact(target, filters=dict()):
# query = select(getattr(ProjectContact, target))
# for name, value in filters.items():
# query = query.where(getattr(ProjectContact, name) == value)
# return query


# def dataset(target, filters=dict()):
# query = select(getattr(Dataset, target))
# for name, value in filters.items():
# query = query.where(getattr(Dataset, name) == value)
# return query

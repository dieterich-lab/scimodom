# template queries

from sqlalchemy import select
from scimodom.database.models import (
    Modification,
    DetectionTechnology,
    Taxa,
    Organism,
    Selection,
    Assembly,
    AssemblyVersion,
    Annotation,
    AnnotationVersion,
    Project,
    ProjectContact,
    Dataset,
    Data,
)


# -- special queries


def get_assembly_version():
    return select(AssemblyVersion.version_num)


def get_annotation_version():
    return select(AnnotationVersion.version_num)


# -- simple query wrappers


def query_column_where(model, column, filters=dict()):
    # query one column w/ or w/o filters
    import scimodom.utils.utils as utils

    try:
        query = select(getattr(model, column))
    except:
        model = utils.get_model(model)
        query = select(getattr(model, column))
    for key, value in filters.items():
        query = query.where(getattr(model, key) == value)
    return query

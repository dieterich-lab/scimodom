# template queries
from sqlalchemy import select

from scimodom.database.models import AssemblyVersion, AnnotationVersion
import scimodom.utils.utils as utils

# -- special queries


def get_assembly_version():
    return select(AssemblyVersion.version_num)


def get_annotation_version():
    return select(AnnotationVersion.version_num)


# -- simple query constructors


def query_column_where(
    model, columns: str | list[str], filters: dict[str, str | int] = dict()
):
    """Query one or more column(s) w/ or w/o filters.

    :param model: Model (or model name)
    :type model: ...
    :columns: Column or list of columns
    :type columns: str | list
    :param filters: Query filters in the form of {column: value}
    :type filters: dict
    """

    columns_list = utils.to_list(columns)
    column = columns_list[0]
    try:
        query = select(getattr(model, column))
    except:
        model = utils.get_model(model)
        query = select(getattr(model, column))
    for column in columns_list[1:]:
        query = query.add_columns(getattr(model, column))
    for key, value in filters.items():
        query = query.where(getattr(model, key) == value)
    return query

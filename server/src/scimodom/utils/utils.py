import inspect
import uuid
from collections.abc import Sequence, Iterable
from itertools import chain
from typing import Any

import shortuuid

import scimodom.database.models as models


def get_model(model: str):
    """Get model class by name.

    :param model: Name of class
    :type model: str
    :returns: The model class
    :rtype: Base
    """

    try:
        return {
            name: cls
            for name, cls in inspect.getmembers(models, inspect.isclass)
            if cls.__module__ == models.__name__
        }[model]
    except Exception:
        msg = f"Model undefined: {model}."
        raise KeyError(msg)


def to_list(i: int | float | str | list | set | None) -> list[Any]:
    """Converts numerical, string, list, set, and None to list,
    but does not unpack tuple or dict.

    :param i: String, list, set, or None
    :type i: str | list | set | None
    :returns: Input as a list
    :rtype: list
    """
    return (
        i
        if isinstance(i, list)
        else list(i)
        if isinstance(i, set)
        else []
        if i is None
        else [i]
    )


def flatten_list(items: list | Sequence | Iterable) -> list:
    """Flatten list.

    :param items: list
    :type items: list
    :returns: flattened list
    :rtype: list
    """

    return list(chain.from_iterable(items))


def gen_short_uuid(length: int, suuids: Sequence[Any]) -> str:
    """Generate a short UUID.

    :param length: Length of ID
    :type length: int
    :param suuids: List of existing IDs
    :type suuids: list
    :returns: Newly created ID
    :rtype: str
    """

    u = uuid.uuid4()
    suuid = shortuuid.encode(u)[:length]
    while suuid in suuids:
        suuid = shortuuid.encode(u)[:length]
    return suuid


def get_ensembl_prefix(gene_id: str) -> str:
    """Extract Ensembl prefix for gene identifier.

    :param gene_id: Gene identifier
    :type gene_id: str
    :returns: Prefix
    :rtype: str
    """
    tmp = gene_id[:7]
    if tmp[-1].isdigit():
        return tmp[:3]
    else:
        return tmp[:6]

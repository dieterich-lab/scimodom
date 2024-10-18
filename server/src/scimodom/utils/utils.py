import uuid
from typing import Any, Sequence

import shortuuid


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

import uuid
from typing import Any

import shortuuid


def to_list(i: int | float | str | list | set | None) -> list[Any]:
    """Convert numerical, string, list, set, and None to list.

    NOTE: Does not unpack tuple or dict.

    :param i: Int, float, str, list, set, or None
    :return: Input as a list
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


def gen_short_uuid(
    length: int,
    suuids: list[str],
    max_attempts: int = 1000,
) -> str:
    """Generate a short UUID that is not in a list of existing IDs.

    :param length: Length of ID
    :param suuids: List of existing IDs
    :param max_attempts: Maximum number of attempts
    :raises RuntimeError: If no unused ID was found after `max_attempts`
    :return: Newly created ID
    """
    existing = set(suuids)
    for _ in range(max_attempts):
        suuid = shortuuid.encode(uuid.uuid4())[:length]
        if suuid not in existing:
            return suuid
    raise RuntimeError(f"Failed to generate a unique ID after {max_attempts} attempts.")

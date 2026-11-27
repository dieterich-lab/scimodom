"""The assembly manifest."""

from datetime import datetime, timezone
from typing import Any

MANIFEST_SCHEMA_VERSION = 1


def build_manifest(
    assembly_info: dict[str, Any],
    provider: str,
    release: int,
    archive: str,
    data_release_response: dict[str, Any] | None = None,
    fetched_at: str | None = None,
) -> dict[str, Any]:
    """Build the manifest of an installed assembly.

    :param assembly_info: Assembly information as reported by the
    provider.
    :param provider: Reference data provider e.g. "ensembl"
    :param release: Release the files were obtained from
    :param archive: Archive token the files were obtained from e.g.
    "jul2023". The URLs are derived from it, cf.
    scimodom.utils.specs.enums.Ensembl.
    :param data_release_response: Raw provider response naming the
    available releases, kept so the source of the claim is not lost
    :param fetched_at: UTC timestamp, defaults to now
    :return: Manifest
    """
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "assembly": assembly_info,
        "source": {
            "provider": provider,
            "release": release,
            "archive": archive,
            "fetched_at": fetched_at or _utc_now(),
            "data_release_response": data_release_response,
        },
    }


def get_coord_system_versions(manifest: dict[str, Any]) -> list[str]:
    """Get the valid assembly names from a manifest.

    :param manifest: Manifest
    :return: Assembly names
    """
    return manifest["assembly"]["coord_system_versions"]


def get_provider(manifest: dict[str, Any]) -> str:
    """Get the provider an assembly was installed from.

    :param manifest: Manifest
    :return: Provider e.g. "ensembl"
    """
    return manifest["source"]["provider"]


def get_release(manifest: dict[str, Any]) -> int:
    """Get the release an assembly was installed from.

    :param manifest: Manifest
    :return: Release
    """
    return manifest["source"]["release"]


def get_archive(manifest: dict[str, Any]) -> str:
    """Get the archive an assembly was installed from.

    :param manifest: Manifest
    :return: Archive token e.g. "jul2023"
    """
    return manifest["source"]["archive"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

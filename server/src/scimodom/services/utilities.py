from functools import cache
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import (
    DetectionMethod,
    DetectionTechnology,
    Modification,
    Modomics,
    Organism,
    RNAType,
    Taxonomy,
    Taxa,
)
from scimodom.services.annotation import BIOTYPES

try:
    from scimodom._build_info import BUILD_INFO
except ModuleNotFoundError:
    BUILD_INFO = None  # dev before running the script

MAPPED_BIOTYPES = sorted(set(BIOTYPES.values()))


class UtilitiesService:
    """Provide a collection of general queries.

    - catalogs
    - DB lookups
    - release
    """

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    @staticmethod
    def get_biotypes() -> dict[str, list[str]]:
        """Get all biotypes.

        NOTE: biotypes are independent of species/RNA type.
        To evaluate dynamically, remove module-level constant,
        and use here mapped_biotypes = sorted(set(BIOTYPES.values()))

        :return: Biotypes values used in the UI
        """
        return {"biotypes": MAPPED_BIOTYPES}

    def get_rna_types(self) -> list[dict[str, Any]]:
        """Get all RNA types.

        :return: Identifier and name (description) from RNAType
        """
        rna_types = self._session.scalars(select(RNAType)).all()
        return [{"id": rna.id, "name": rna.name} for rna in rna_types]

    def get_taxa(self) -> list[dict[str, Any]]:
        """Get all species with their taxonomy.

        :return: Identifier, name and short name from Taxa; domain,
        kingdom, and phylum from Taxonomy.
        """
        rows = self._session.execute(
            select(Taxa, Taxonomy).join(Taxonomy, Taxa.inst_taxonomy)
        )
        return [
            {
                "taxa_id": row.Taxa.id,
                "taxa_name": row.Taxa.name,
                "taxa_short_name": row.Taxa.short_name,
                "domain": row.Taxonomy.domain,
                "kingdom": row.Taxonomy.kingdom,
                "phylum": row.Taxonomy.phylum,
            }
            for row in rows
        ]

    def get_modomics(self) -> list[dict[str, Any]]:
        """Get all modifications.

        :return: Identifier (MODOMICS code) and short name from Modomics
        """
        modomics = self._session.scalars(select(Modomics)).all()
        return [
            {"id": mod.id, "modomics_short_name": mod.short_name} for mod in modomics
        ]

    def get_modomics_id_by_short_name(self, name: str) -> str:
        """Get MODOMICS ID by short name.

        :param name: MODOMICS short name
        :raises NoResultFound:
        :return: MODOMICS ID
        """
        return (
            get_session()
            .execute(select(Modomics.id).filter_by(short_name=name))
            .scalar_one()
        )

    def get_methods(self) -> list[dict[str, Any]]:
        """Get all detection methods.

        :return: Identifier, class, and method from DetectionMethod
        """
        methods = self._session.scalars(select(DetectionMethod)).all()
        return [
            {"id": method.id, "cls": method.cls, "meth": method.meth}
            for method in methods
        ]

    def get_method_id_by_name(self, name: str) -> str:
        """Get detection method ID by method name.

        :param name: Method name (meth)
        :raises NoResultFound:
        :return: DetectionMethod ID
        """
        return (
            get_session()
            .execute(select(DetectionMethod.id).filter_by(meth=name))
            .scalar_one()
        )

    def get_modification_id(self, rna: str, modomics_id: str) -> int:
        """Get Modification ID by RNA type and MODOMICS ID.

        :param rna: RNA type
        :param modomics_id: MODOMICS ID
        :raises NoResultFound:
        :return: Modification ID
        """
        return self._session.execute(
            select(Modification.id).filter_by(rna=rna, modomics_id=modomics_id)
        ).scalar_one()

    def get_organism_id(self, taxa_id: int, cto: str) -> int:
        """Get Organism ID by taxonomy ID and cell/tissue/organ.

        :param taxa_id: Taxonomy ID
        :param cto: Cell/tissue/organ
        :raises NoResultFound:
        :return: Organism ID
        """
        return self._session.execute(
            select(Organism.id).filter_by(taxa_id=taxa_id, cto=cto)
        ).scalar_one()

    def get_technology_id(self, method_id: str, tech: str) -> int:
        """Get DetectionTechnology ID by method ID and technology name.

        :param method_id: DetectionMethod ID
        :param tech: Technology name
        :raises NoResultFound:
        :return: DetectionTechnology ID
        """
        return self._session.execute(
            select(DetectionTechnology.id).filter_by(method_id=method_id, tech=tech)
        ).scalar_one()

    def get_release_info(self) -> dict[str, Any]:
        """Get build, API and data-release information.

        :return: Build metadata, API version, DB revision status.
        """
        return {
            "build": BUILD_INFO["build"] if BUILD_INFO else None,
            "api": BUILD_INFO["api"] if BUILD_INFO else None,
            "database": {
                **(BUILD_INFO["database"] if BUILD_INFO else {}),
                "current_revision": self._get_current_db_revision(),
            },
        }

    def _get_current_db_revision(self) -> str | None:
        try:
            return self._session.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar()
        except Exception:
            return None


@cache
def get_utilities_service() -> UtilitiesService:
    """Instantiate a UtilitiesService object.

    :return: UtilitiesService instance
    """
    return UtilitiesService(
        session=get_session(),
    )

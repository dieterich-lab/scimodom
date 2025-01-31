from collections import defaultdict
from functools import cache
from json import dumps
from subprocess import run
from typing import TextIO

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import (
    Modomics,
    Taxa,
    Organism,
    DetectionTechnology,
    Data,
    Modification,
    Dataset,
    DatasetModificationAssociation,
)
from scimodom.services.file import FileService, get_file_service
from scimodom.utils.specs.enums import SunburstChartType


class SunburstService:
    """Utility class to update and retrieve Sunburst charts data.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param file_service: File service instance
    :type file_service: FileService
    """

    def __init__(
        self,
        session: Session,
        file_service: FileService,
    ) -> None:
        self._session = session
        self._file_service = file_service

    @staticmethod
    def trigger_background_update() -> None:
        """Trigger update in the background using the CLI."""
        run(["flask", "--app", "scimodom.app", "charts", "sunburst-update"])

    def open_json(self, chart_type: SunburstChartType) -> TextIO:
        """Open a chart json data file.

        Attempt to create file if does not exist.

        :param chart_type: Chart type
        :type chart_type: SunburstChartType
        :return: Opened file handle for reading
        :rtype: TextIO
        """
        try:
            return self._file_service.open_sunburst_cache(chart_type.value)
        except FileNotFoundError:
            self.update_cache(chart_type)
            return self._file_service.open_sunburst_cache(chart_type.value)

    def update_cache(self, chart_type: SunburstChartType) -> None:
        """Update Sunburst charts data.

        Generate content, and pass it to the FileService.

        :param chart_type: Chart type
        :type chart_type: SunburstChartType
        """
        query = self._get_query(chart_type)
        result = self._session.execute(query).fetchall()
        json_data = self._get_data_from_result(chart_type, result)
        as_string = dumps(json_data)

        def generator():
            yield as_string

        self._file_service.update_sunburst_cache(chart_type.value, generator())

    def do_background_update(self):
        """Provide the actual background update method."""

        def update_all():
            for chart_type in SunburstChartType:
                self.update_cache(chart_type)

        self._file_service.run_sunburst_update(update_all)

    @staticmethod
    def _get_data_from_result(chart_type, result):
        structure = defaultdict(
            lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        )
        for mod_name, species_name, org_name, tech_name, count in result:
            structure[mod_name][species_name][org_name][tech_name] = count
        json_data = [
            {
                "name": chart_type.value.capitalize(),
                "children": [
                    {
                        "name": mod,
                        "children": [
                            {
                                "name": species,
                                "children": [
                                    {
                                        "name": org,
                                        "children": [
                                            {"name": tech, "size": size}
                                            for tech, size in techs.items()
                                        ],
                                    }
                                    for org, techs in orgs.items()
                                ],
                            }
                            for species, orgs in species_data.items()
                        ],
                    }
                    for mod, species_data in structure.items()
                ],
            }
        ]
        return json_data

    @staticmethod
    def _get_query(chart_type):
        query = select(
            Modomics.short_name.label("modification_name"),
            Taxa.short_name.label("species_name"),
            Organism.cto.label("organism_name"),
            DetectionTechnology.tech.label("technology_name"),
            func.count().label("technology_count"),
        )
        if chart_type == SunburstChartType.search:
            query = (
                query.select_from(Data)
                .join(Modification, Data.modification_id == Modification.id)
                .join(Modomics, Modification.modomics_id == Modomics.id)
                .join(Dataset, Data.dataset_id == Dataset.id)
                .join(Organism, Dataset.organism_id == Organism.id)
                .join(Taxa, Organism.taxa_id == Taxa.id)
                .join(
                    DetectionTechnology, Dataset.technology_id == DetectionTechnology.id
                )
            )
        else:
            query = (
                query.select_from(Dataset)
                .join(
                    DatasetModificationAssociation,
                    Dataset.id == DatasetModificationAssociation.dataset_id,
                )
                .join(
                    Modification,
                    DatasetModificationAssociation.modification_id == Modification.id,
                )
                .join(Modomics, Modification.modomics_id == Modomics.id)
                .join(Organism, Dataset.organism_id == Organism.id)
                .join(Taxa, Organism.taxa_id == Taxa.id)
                .join(
                    DetectionTechnology, Dataset.technology_id == DetectionTechnology.id
                )
            )
        return query.group_by(
            Modomics.short_name, Taxa.short_name, Organism.cto, DetectionTechnology.tech
        )


@cache
def get_sunburst_service() -> SunburstService:
    """Instantiate a SunburstService object by injecting its dependencies.

    :returns: Sunburst service instance
    :rtype: SunburstService
    """
    return SunburstService(
        session=get_session(),
        file_service=get_file_service(),
    )

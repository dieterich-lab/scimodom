#! /usr/bin/env python3

# import scimodom.utils.utils as utils

from scimodom.database.models import Dataset, Association

import scimodom.database.queries as queries

from sqlalchemy import select, func

import logging

logger = logging.getLogger(__name__)


class DuplicateDatasetError(Exception):
    pass


class DataService:
    def __init__(
        self,
        session,
        smid,
        title,
        taxa_id,
        assembly_id,
        modification_ids,
        technology_ids,
        organism_ids,
    ):
        self._session = session

        self._smid = smid
        self._title = title

        self._taxa_id = taxa_id
        self._assembly_id = assembly_id

        self._modification_ids  # list - selection from FE upload form - eventually check with file content?
        self._technology_id  # for now just one
        self._organism_id  # for now just one

        self._lifted = False

    def _validate_entry(self):
        for mod_id in self._modification_ids:
            query = queries.query_column_where(
                "Selection",
                "id",
                filters={
                    "modification_id": mod_id,
                    "technology_id": self._technology_id,
                    "organism_id": self._organism_id,
                },
            )
            selection_id = self._session.execute(query).scalar()
            if not selection_id:
                continue
            query = (
                select(func.distinct(Dataset.id))
                .outerjoin(Association, Dataset.id == Association.dataset_id)
                .where(
                    Association.selection_id == selection_id,
                    Dataset.project_id == self._smid,
                    Dataset.title == self._title,
                    Dataset.assembly_id == self._assembly_id,
                )
            )
            eufid = self._session.execute(query).scalar()
            if eufid:
                msg = (
                    f"A similar record with EUFID = {eufid} already exists for project {self._smid}. "
                    f"Aborting transaction!"
                )
                raise DuplicateDatasetError(msg)

    def _validate_assembly(self):
        query = queries.get_assembly_version()
        db_assembly_version = self._session.execute(query).scalar()

        query = queries.query_column_where(
            "Assembly", "version", filters={"id": self._assembly_id}
        )
        assembly_version = self._session.execute(query).scalar()

        if not assembly_version == db_assembly_version:
            self._lifted = True
            print("Some message... do something when?")

    def create_dataset(self):
        self._validate_entry()
        self._validate_assembly()

        # self._create_eufid()
        # query = select(Dataset.id)
        # eufids = self._session.execute(query).scalars().all()
        # self._eufid = utils.gen_short_uuid(self.EUFID_LENGTH, eufids)
        # read data - instantiate importer, parseEUF
        # confirm/commit

        # self._add_association()
        # TODO: we also need a method to assign assocaition table from input
        # so we need to have selection.id (or query from modification, technology, organism)
        # these fields are presumably filled at upload on the FE form (after being available
        # via SMID/projetc creation).
        # if via API/maintenance, we need to provide these as args, to get selection.id
        # and make sure they are valid choices.

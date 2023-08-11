#! /usr/bin/env python3

import scimodom.utils.utils as utils

from scimodom.database.models import Project, ProjectSource

from sqlalchemy import select, func

import logging

logger = logging.getLogger(__name__)


class DuplicateProjectError(Exception):
    pass


class ProjectService:
    
    # >>> ProjectService(get_session(), project) 
    def __init__(self, session, project):
        self._session = session
        self._project = project
    
    
    def _validate_keys(self):
        
        from itertools import chain
        
        cols = utils.get_table_columns("Project", remove=["id", "date_added"])
        cols.extend(["external_sources", "metadata"])
        utils.check_keys_exist(self._project.keys(), cols)
    
        if self._project["external_sources"] is not None:
            keys = list(set(chain.from_iterable(utils.to_list(self._project["external_sources"]))))
            cols = utils.get_table_columns("ProjectSource", ["id", "project_id"])
            utils.check_keys_exist(keys, cols)
            
        keys = list(set(chain.from_iterable(utils.to_list(self._project["metadata"]))))
        cols = utils.get_table_columns("Modification", remove=["id"])
        cols.extend(utils.get_table_columns("DetectionTechnology", remove=["id"]))
        utils.check_keys_exist(keys, cols)
        
        keys = utils.to_list(self._project["metadata"])[0]["organism"].keys()
        cols = utils.get_table_columns("Organism", remove=["id"])
        cols.append("assembly")
        utils.check_keys_exist(keys, cols)
             
    
    def _get_prj_src(self):
    
        from sqlalchemy import tuple_, and_, or_
        
        ors = or_(False)
        ands = and_(True)
        
        for s in utils.to_list(self._project["external_sources"]):
            doi = s["doi"]
            pmid = s["pmid"]
            if doi is None:
                if pmid is not None:
                    ands = and_(ProjectSource.doi.is_(None), ProjectSource.pmid.in_([pmid]))
                else:
                    ands = and_(ProjectSource.doi.is_(None), ProjectSource.pmid.is_(None))
            elif pmid is None:
                ands = and_(ProjectSource.doi.in_([doi]), ProjectSource.pmid.is_(None))
            else:
                ands = tuple_(ProjectSource.doi, ProjectSource.pmid).in_([tuple([doi, pmid])])
            ors = or_(ors, ands)
        return ors


    def _validate_entry(self):
        
        query = (
            select(
                func.distinct(Project.id)
            )
            .outerjoin(ProjectSource, Project.id == ProjectSource.project_id)
            .where(Project.title == self._project['title'])
            )
        query = query.where(self._get_prj_src())
        smid = self._session.execute(query).scalar()
        if smid:
            msg = f"A similar record with SMID = {smid} already exists. " \
                  f"Query based on a combination of title = {self._project['title']}, " \
                  f"and published sources (DOI = {self._project['doi']}, " \
                  f"PMID = {self._project['pmid']}), where available. Aborting transaction!"
            raise DuplicateProjectError(msg)
        
    
    def _create_smid(self):
        
        import uuid
        import shortuuid
        
        from datetime import datetime, timezone
        
        SMID_LENGTH = 8
        
        query = select(Project.id)
        smids = self._session.execute(query).scalars().all()

        u = uuid.uuid4()
        smid = shortuuid.encode(u)[:SMID_LENGTH]
        while smid in smids:
            smid = shortuuid.encode(u)[:SMID_LENGTH]
        
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        
        return smid, stamp
    
        
    def create_project(self):
        
        self._validate_keys()
        self._validate_entry()
            
        smid, stamp = self._create_smid()
        # stamp is string ?
        print(f"{smid}, {stamp}")
        
        # add missing selection to DB


        # add project to DB
            
        # testing: keys combination
        # testing: add new project, add existing project, external_sources, metadata combination
        # testing: add missing selection or not ?

        # what to do with assembly?

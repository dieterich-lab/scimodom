#! /usr/bin/env python3

import json

from argparse import ArgumentParser, SUPPRESS
import logging

#from scimodom.database.models import Project, ProjectSource

from scimodom.database.database import Session, init

import scimodom.utils.utils as utils

from scimodom.services.project import ProjectService

logger = logging.getLogger(__name__)





def main():
    parser = ArgumentParser(add_help=False,
                            description="""Add new project to DB - create SMID.""")
    
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')

    required.add_argument('-p', '--project', help="""INSERT new project using [--project PROJECT], 
                          where PROJECT is a json file with required fields""", type=str, required=True)
    
    optional.add_argument('-h', '--help', action='help', default=SUPPRESS, 
                          help='show this help message and exit')
    
    utils.add_log_opts(parser)
    args = parser.parse_args()
    utils.update_logging(args)
    
    # init DB
    init(lambda: Session)
    # load project metadata
    project = json.load(open(args.project))
    
    #from scimodom.database.database import get_session
    #ProjectService(get_session(), project).create_project()
    # ?
    ProjectService(Session(), project).create_project()
    
    print("continue")
    

if __name__ == '__main__':
    main()

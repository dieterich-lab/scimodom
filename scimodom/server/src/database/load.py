#! /usr/bin/env python3

# draft script to access the DB outside the app, ie. w/o running the app
# for loading/updating tables

# import models, session and engine from app


from pathlib import Path
import sys
path_root = Path(__file__).parents[2]
sys.path.append(str(path_root))
print(sys.path)

print(f"Name: {__name__}")
print(f"Package: {__package__}")

#import importlib
#module = importlib.import_module("subdir.example")

import argparse
import logging

import pandas as pd

#from . import models
#from .database import Session, init

import models
from database import Session, init

init()
#session = Session()

logger = logging.getLogger(__name__)    
    
import inspect

from sqlalchemy.dialects.mysql import insert

def get_model(model):
    return {
        name: cls for name, cls in inspect.getmembers(models, inspect.isclass)
        if cls.__module__ == models.__name__
    }[model]


def confirm(msg):
    """
    Ask user to enter Y or N (case-insensitive).

    :return: True if the answer is Y.
    :rtype: bool
    """
    answer = ""
    while answer not in ["y", "n"]:
        prompt = f"{msg}\nConfirm to continue [Y/N]? "
        answer = input(prompt).lower()
    return answer == "y"


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description="""Update DB""")


    parser.add_argument('-m', '--model', help="""Upsert MODEL using [--table TABLE]. 
                        Performs an INSERT... ON DUPLICATE KEY UPDATE. Requires [--table TABLE]""", 
                        type=str, required="--table" in sys.argv)
    
    parser.add_argument('-t', '--table', help="""Database table for MODEL with column 
                        names. Only columns matching __table__.columns are used.                        
                        CSV format. Requires [--model MODEL]""", type=str, 
                        required="--model" in sys.argv)
    
    logging_options = parser.add_argument_group("logging options")
    default_log_file = ""
    logging_level_choices = ['NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    default_logging_level = 'WARNING'
    format_str='%(levelname)-8s %(name)-8s %(asctime)s : %(message)s'
    logging_options.add_argument('--log-file', help="Log file", default=default_log_file)
    logging_options.add_argument('--logging-level', help="Logging level", choices=logging_level_choices,
        default=default_logging_level)
    
    args = parser.parse_args()
    
    # TODO: add logging utils
    level = logging.getLevelName(args.logging_level)
    logger.setLevel(level)
    
    if args.log_file:
        h = logging.FileHandler(args.log_file)
        h.setLevel(level)
        formatter = logging.Formatter(format_str)
        h.setFormatter(formatter)
        logger.addHandler(h)
        
        
    if args.model:
        
        try:
            model = get_model(args.model)
        except:
            msg = f"Undefined --model {args.model}. Terminating!"
            logger.error(msg)
            return
        # columns
        cols = set([column.key for column in model.__table__.columns])
        table = pd.read_csv(args.table)
        table = table.loc[:, table.columns.isin(cols)]
        if table.shape[1] == 1:
            msg = f"Only {table.columns.tolist()[0]} found in TABLE. Terminating!"
            logger.error(msg)
            return
        msg = f"Using {args.model} to update table {model.__table__.name} with " \
              f"the following columns {table.columns.tolist()}."
        if not confirm(msg):
            return
        # upsert DB NOTE:
        values = table.to_dict(orient="records")
        #stmt = insert(model).values(values)
        #ucols = {c.name: c for c in stmt.inserted} # filter id column ?
        #stmt = stmt.on_duplicate_key_update(**ucols) # upsert statement, expand columns dict
        #conn.execute(ups_stmt)
        #conn.commit()
        
        with Session() as session, session.begin():
            stmt = insert(model).values(values)
            ucols = {c.name: c for c in stmt.inserted} # filter id column ?
            stmt = stmt.on_duplicate_key_update(**ucols) # upsert statement, expand columns dict
            session.execute(stmt)

        # inner context calls session.commit(), if there were no exceptions
        # outer context calls session.close()
        


    else:
        
        logger.info("NOTHING")
    
    
if __name__ == '__main__':
    main()
    
#with open(file) as f:
    #csv_reader = csv.DictReader(f)


    #for row in csv_reader:
        #db_record = models.Record(name=row["name"], ...)
        #db.add(db_record)
        
        
    #db.commit()
    
#db.close()

from pathlib import Path
import sys
path_root = Path(__file__).parents[2]
sys.path.append(str(path_root))


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# hard coded here now - TODO: config
DATABASE = "mysql+mysqldb://eboileau:@localhost/scimodom"

# options -> pool_recycle, isolation_level
# connect_args={"check_same_thread": False}
engine = create_engine(DATABASE)

Session = sessionmaker(autocommit=False,
                       autoflush=False,
                       bind=engine)

# from sqlalchemy.orm import scoped_session
# in app import Session, then define app.session = scoped_session(Session)


class Base(DeclarativeBase):
    pass

def init():
    
    #from . import models
    import models
    Base.metadata.create_all(engine)
    
    


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

_session = None


# hard coded here now - TODO: config
DATABASE = "mysql+mysqldb://eboileau:@localhost/scimodom"

# options -> pool_recycle, isolation_level
# connect_args={"check_same_thread": False}
engine = create_engine(DATABASE)

Session = sessionmaker(autocommit=False,
                       autoflush=False,
                       bind=engine)



class Base(DeclarativeBase):
    pass


def get_session():
    if _session is None:
        raise Exception("Session not initialized!")
    else:
        return _session()
    
    
def init(session):
    
    global _session
    _session = session
    
    import scimodom.database.models
    Base.metadata.create_all(engine)
    
    

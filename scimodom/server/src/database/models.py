

from .database import Base

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Modomics(Base):
    __tablename__ = "modomics"
    
    id: Mapped[str] = mapped_column(primary_key=True)
    lname: Mapped[str] = mapped_column()
    sname: Mapped[str] = mapped_column(String(30))
    moiety: Mapped[str] = mapped_column(String(30))
    
    instances: Mapped[List["Modification"]] = relationship(back_populates="instance")
    
class Modification(Base):
    __tablename__ = "modification"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    rna: Mapped[str] = mapped_column(String(30))
    code: Mapped[str] = mapped_column(ForeignKey("modomics.id"))
    
    instance: Mapped["Modomics"] = relationship(back_populates="instances")
    
 
 class DetectionMethod(Base):
    __tablename__ = "method"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    cls: Mapped[str] = mapped_column(String(30))
    meth: Mapped[str] = mapped_column()
    
    instances: Mapped[List["DetectionTechnology"]] = relationship(back_populates="instance")
    
    
 class DetectionTechnology(Base):
    __tablename__ = "technology"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    tech: Mapped[str] = mapped_column()
    methid: Mapped[int] = mapped_column(ForeignKey("method.id"))
    
    instance: Mapped["DetectionMethod"] = relationship(back_populates="instances")
    
    
class Taxonomy(Base):
    __tablename__ = "taxonomy"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    domain: Mapped[str] = mapped_column(String(30))
    kingdom: Mapped[str] = mapped_column(String(30))
    phylum: Mapped[str] = mapped_column(String(30))
    
    instances: Mapped[List["Organism"]] = relationship(back_populates="instance")
    
    
class Organism(Base):
    __tablename__ = "organism"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    species: Mapped[str] = mapped_column()
    cto: Mapped[str] = mapped_column()
    taxid: Mapped[int] = mapped_column(ForeignKey("taxonomy.id"))
    
    instance: Mapped["Taxonomy"] = relationship(back_populates="instances")
    
    
    
    
    
    
 
 

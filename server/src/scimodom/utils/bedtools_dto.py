from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, Field, model_validator

NoneNegativInt = Annotated[int, Field(ge=0)]
Score = Annotated[int, Field(ge=0, le=1000)]
PercentInt = Annotated[int, Field(ge=0, le=100)]
DatasetId = Annotated[str, Field(min_length=12, max_length=12)]


NO_SUCH_DATASET_ID = "NoSuchDataSet_"  # Used when we generate a ModificationRecord, not orignating form our database


class Strand(Enum):
    FORWARD = "+"
    REVERSE = "-"


class ModificationRecord(BaseModel):
    chrom: str = Annotated[str, Field(min_length=1, max_length=128)]
    start: int = NoneNegativInt
    end: int = NoneNegativInt
    name: str = Annotated[str, Field(min_length=1, max_length=32)]
    score: int = Score
    strand: Strand
    coverage: int = NoneNegativInt
    frequency: int = PercentInt
    dataset_id: str = DatasetId

    @model_validator(mode="after")
    def check_start_end(self):
        if self.end <= self.start:
            raise ValueError(
                f"The value of 'end' ({self.end}) must be greater than the value of 'start' ({self.start})"
            )


class SubtractRecord(ModificationRecord):
    pass


class IntersectRecord(BaseModel):
    a: ModificationRecord
    b: ModificationRecord


class ClosestRecord(BaseModel):
    a: ModificationRecord
    b: ModificationRecord
    distance: int


class GenomicAnnotationRecord(BaseModel):
    id: str = Annotated[str, Field(min_length=1, max_length=128)]
    annotation_id: int = NoneNegativInt
    name: str = Optional[Annotated[str, Field(min_length=1, max_length=128)]]
    biotype: str = Optional[Annotated[str, Field(min_length=1, max_length=255)]]


class DataAnnotationRecord(BaseModel):
    gene_id: str = Annotated[str, Field(min_length=1, max_length=128)]
    data_id: int = NoneNegativInt
    feature: str = Annotated[str, Field(min_length=1, max_length=32)]

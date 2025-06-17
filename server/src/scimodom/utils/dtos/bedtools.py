from decimal import Decimal
from typing import Annotated, Optional, Self

from pydantic import BaseModel, NonNegativeInt, PositiveInt, Field, model_validator

from scimodom.utils.specs.enums import Strand

# sqlalchemy.Numeric(precision=5, scale=2, asdecimal=True)
NonNegativePercent = Annotated[Decimal, Field(ge=0, le=100)]

DatasetId = Annotated[str, Field(min_length=12, max_length=12)]


class Bed6Record(BaseModel):
    chrom: Annotated[str, Field(min_length=1, max_length=128)]
    start: NonNegativeInt
    end: NonNegativeInt
    name: Annotated[str, Field(min_length=1, max_length=128)]
    score: PositiveInt
    strand: Strand

    @model_validator(mode="after")
    def check_start_end(self) -> Self:
        if self.end <= self.start:
            raise ValueError(
                f"The value of 'end' ({self.end}) must be greater than the value of 'start' ({self.start})"
            )
        return self


class EufRecord(Bed6Record):
    thick_start: NonNegativeInt
    thick_end: NonNegativeInt
    item_rgb: str
    coverage: PositiveInt
    frequency: NonNegativePercent

    @model_validator(mode="after")
    def check_thick_start_end(self) -> Self:
        if self.thick_end <= self.thick_start:
            raise ValueError(
                f"The value of 'thickEnd' ({self.thick_end}) must be greater than the value of 'thickStart' ({self.thick_start})"
            )
        return self


class ComparisonRecord(Bed6Record):
    coverage: PositiveInt
    frequency: NonNegativePercent
    eufid: DatasetId


class SubtractRecord(ComparisonRecord):
    pass


class IntersectRecord(BaseModel):
    a: ComparisonRecord
    b: ComparisonRecord


class ClosestRecord(BaseModel):
    a: ComparisonRecord
    b: ComparisonRecord
    distance: int


class GenomicAnnotationRecord(BaseModel):
    id: Annotated[str, Field(min_length=1, max_length=128)]
    annotation_id: NonNegativeInt
    name: Optional[Annotated[str, Field(min_length=1, max_length=128)]] = None
    biotype: Optional[Annotated[str, Field(min_length=1, max_length=255)]] = None


class DataAnnotationRecord(BaseModel):
    gene_id: Annotated[str, Field(min_length=1, max_length=128)]
    data_id: NonNegativeInt
    feature: Annotated[str, Field(min_length=1, max_length=32)]

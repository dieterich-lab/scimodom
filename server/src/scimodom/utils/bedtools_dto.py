from typing import Annotated, Optional, Self

from pydantic import BaseModel, Field, model_validator

from scimodom.utils.common_dto import Strand

NonNegativInt = Annotated[int, Field(ge=0)]
Score = Annotated[int, Field(ge=0, le=1000)]
PositivePercentInt = Annotated[int, Field(gt=0, le=100)]
DatasetId = Annotated[str, Field(min_length=12, max_length=12)]


class Bed6Record(BaseModel):
    chrom: Annotated[str, Field(min_length=1, max_length=128)]
    start: NonNegativInt
    end: NonNegativInt
    name: Annotated[str, Field(min_length=1, max_length=32)]
    score: Score
    strand: Strand

    @model_validator(mode="after")
    def check_start_end(self) -> Self:
        if self.end <= self.start:
            raise ValueError(
                f"The value of 'end' ({self.end}) must be greater than the value of 'start' ({self.start})"
            )
        return self


class EufRecord(Bed6Record):
    thick_start: NonNegativInt
    thick_end: NonNegativInt
    item_rgb: str
    coverage: NonNegativInt
    frequency: PositivePercentInt

    @model_validator(mode="after")
    def check_thick_start_end(self) -> Self:
        if self.thick_end <= self.thick_start:
            raise ValueError(
                f"The value of 'thickEnd' ({self.thick_end}) must be greater than the value of 'thickStart' ({self.thick_start})"
            )
        return self


class ComparisonRecord(Bed6Record):
    coverage: NonNegativInt
    frequency: PositivePercentInt
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
    annotation_id: NonNegativInt
    name: Optional[Annotated[str, Field(min_length=1, max_length=128)]] = None
    biotype: Optional[Annotated[str, Field(min_length=1, max_length=255)]] = None


class DataAnnotationRecord(BaseModel):
    gene_id: Annotated[str, Field(min_length=1, max_length=128)]
    data_id: NonNegativInt
    feature: Annotated[str, Field(min_length=1, max_length=32)]

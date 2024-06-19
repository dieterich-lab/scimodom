from typing import Annotated, Optional, Self

from pydantic import BaseModel, Field, model_validator

from scimodom.utils.common_dto import Strand

NonNegativInt = Annotated[int, Field(ge=0)]
Score = Annotated[int, Field(ge=0, le=1000)]
PercentInt = Annotated[int, Field(ge=0, le=100)]
DatasetId = Annotated[str, Field(min_length=12, max_length=12)]


class Bed6Record(BaseModel):
    chrom: str = Annotated[str, Field(min_length=1, max_length=128)]
    start: int = NonNegativInt
    end: int = NonNegativInt
    name: str = Annotated[str, Field(min_length=1, max_length=32)]
    score: int = Score
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
    frequency: PercentInt

    @model_validator(mode="after")
    def check_thick_start_end(self) -> Self:
        if self.thick_end <= self.thick_start:
            raise ValueError(
                f"The value of 'thickEnd' ({self.thick_end}) must be greater than the value of 'thickStart' ({self.thick_start})"
            )
        return self


class ComparisonRecord(Bed6Record):
    coverage: NonNegativInt
    frequency: PercentInt
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
    id: str = Annotated[str, Field(min_length=1, max_length=128)]
    annotation_id: int = NonNegativInt
    name: Optional[Annotated[str, Field(min_length=1, max_length=128)]] = None
    biotype: Optional[Annotated[str, Field(min_length=1, max_length=255)]] = None


class DataAnnotationRecord(BaseModel):
    gene_id: str = Annotated[str, Field(min_length=1, max_length=128)]
    data_id: int = NonNegativInt
    feature: str = Annotated[str, Field(min_length=1, max_length=32)]

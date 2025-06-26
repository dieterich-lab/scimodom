from typing import Annotated

from pydantic import BaseModel, Field


class DatasetPostRequest(BaseModel):
    smid: Annotated[str, Field(min_length=1, max_length=8)]
    file_id: str
    rna_type: Annotated[str, Field(min_length=1, max_length=32)]
    modification_id: list[Annotated[int, Field(gt=0)]]
    organism_id: Annotated[int, Field(gt=0)]
    assembly_id: Annotated[int, Field(gt=0)]
    technology_id: Annotated[int, Field(gt=0)]
    title: Annotated[str, Field(min_length=1, max_length=255)]

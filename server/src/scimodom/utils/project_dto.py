from datetime import datetime
from typing import Annotated, Optional, Self

from pydantic import BaseModel, EmailStr, Field, model_validator

from scimodom.utils.utils import to_list


class ProjectSourceDto(BaseModel):
    doi: Optional[Annotated[str, Field(min_length=1, max_length=255)]] = None
    pmid: Optional[Annotated[int, Field(gt=0)]] = None

    @model_validator(mode="after")
    def check_at_least_one(self) -> Self:
        if self.doi is None and self.pmid is None:
            raise ValueError("Need at least 'doi' or 'pmid'")
        return self


class ProjectOrganismDto(BaseModel):
    taxa_id: Annotated[int, Field(gt=0)]
    cto: Annotated[str, Field(min_length=1, max_length=255)]
    assembly_name: Annotated[str, Field(min_length=1, max_length=128)]
    assembly_id: Optional[Annotated[int, Field(gt=0)]] = None


class ProjectMetaDataDto(BaseModel):
    rna: Annotated[str, Field(min_length=1, max_length=32)]
    modomics_id: Annotated[str, Field(min_length=1, max_length=128)]
    tech: Annotated[str, Field(min_length=1, max_length=255)]
    method_id: Annotated[str, Field(min_length=1, max_length=8)]
    organism: ProjectOrganismDto
    note: str | None = None


class ProjectTemplate(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=255)]
    summary: str
    contact_name: Annotated[str, Field(min_length=1, max_length=128)]
    contact_institution: Annotated[str, Field(min_length=1, max_length=255)]
    contact_email: EmailStr
    date_published: datetime | None = None
    external_sources: list[ProjectSourceDto]
    metadata: list[ProjectMetaDataDto]

    @model_validator(mode="before")
    def clean_up(self) -> Self:
        external_sources = self.get("external_sources")
        self["external_sources"] = to_list(external_sources)
        metadata = self.get("metadata")
        self["metadata"] = to_list(metadata)
        if len(self["metadata"]) == 0:
            raise ValueError("Need at least one metadata template")
        return self

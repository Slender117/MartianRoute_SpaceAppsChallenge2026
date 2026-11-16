from pydantic import BaseModel, Field

from app.schemas.route import Provenance


class Assumption(BaseModel):
    id: str
    label: str
    value: float | str | None = Field(description="No value while a source is missing")
    unit: str | None = None
    provenance: Provenance
    source: str = Field(description="Reference, or the [__] marker if the source is still pending")
    note: str | None = None


class AssumptionsResponse(BaseModel):
    parameters: list[Assumption]
    limits: list[str]

from pydantic import BaseModel, Field

from app.schemas.route import Provenance


class Assumption(BaseModel):
    id: str
    label: str
    value: float | str | None = Field(description="Sin valor mientras falte una fuente")
    unit: str | None = None
    provenance: Provenance
    source: str = Field(description="Referencia, o el marcador [__] si la fuente sigue pendiente")
    note: str | None = None


class AssumptionsResponse(BaseModel):
    parameters: list[Assumption]
    limits: list[str]

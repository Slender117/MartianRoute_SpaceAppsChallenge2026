from pydantic import BaseModel, Field

from app.schemas.route import LatLon, Provenance, SuitLimits


class SafeReturnRequest(BaseModel):
    region: str
    base: LatLon | None = Field(
        None, description="Base node; if missing, the region's base is used"
    )
    suit: SuitLimits = SuitLimits()


class SafeReturnResponse(BaseModel):
    """Walk-back time to base from each cell of the region."""

    region: str
    base: LatLon
    shape: tuple[int, int] = Field(description="(rows, columns) of the grid, as in the manifest")
    bbox: tuple[float, float, float, float]
    return_minutes: str = Field(
        description="Return minutes per cell: little-endian uint16 in base64, row by row,"
        " starting at the north row (lat_max), like the region grids"
    )
    no_return_value: int = Field(description="Value of cells with no possible return")
    planned_limit_min: float = Field(
        description="Maximum return so that out, fixed task and return fit the plannable"
        " autonomy (autonomy minus the stricter reserve: 20 % or 30 min)"
    )
    total_limit_min: float = Field(
        description="Maximum return using the whole autonomy, reserve included. Between this"
        " limit and the plannable one, you only get back by using the reserve"
    )
    planned_area_fraction: float = Field(description="Fraction of the region inside the limit")
    total_area_fraction: float = Field(description="Fraction inside the total limit")
    unreachable_fraction: float = Field(description="Fraction with no path back")
    max_eva_dose_msv: float = Field(
        description="Background dose of an EVA that uses the whole plannable autonomy"
    )
    synthetic_data: bool
    provenance: dict[str, Provenance] = {
        "return_minutes": Provenance.modeled,
        "planned_limit_min": Provenance.modeled,
        "total_limit_min": Provenance.modeled,
        "planned_area_fraction": Provenance.modeled,
        "total_area_fraction": Provenance.modeled,
        "unreachable_fraction": Provenance.derived,
        "max_eva_dose_msv": Provenance.modeled,
    }

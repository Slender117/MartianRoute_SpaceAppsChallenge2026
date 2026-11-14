"""Textos en inglés del panel "Supuestos y límites" (GET /assumptions?lang=en).

Solo traduce textos: los valores, las unidades numéricas y las fuentes salen de assumptions.py. Un
parámetro o un límite sin traducción aquí se muestra en español, así que agregar uno nuevo en
assumptions.py no rompe nada; solo hay que sumar aquí su texto en inglés.
"""

from app.engine.assumptions import LIMITS
from app.schemas.assumptions import Assumption, AssumptionsResponse

LUNAR_ON_MARS = "Lunar (Artemis) value applied to Mars: Mars EVAs are still being planned."

# id -> (etiqueta, nota). La nota None deja la nota original (vacía en esos parámetros).
PARAMETERS_EN: dict[str, tuple[str, str | None]] = {
    "base_speed": (
        "Suited walking speed on flat ground",
        f"Over nearly flat regolith, with no slope or rocks. {LUNAR_ON_MARS}",
    ),
    "tobler_coefficient": (
        "Tobler function coefficient",
        "A walking function for people on Earth, scaled to the suited speed.",
    ),
    "o2_rate": ("O₂ use per person", None),
    "o2_flat_per_m": (
        "O₂ per meter on flat ground",
        "O₂ use ÷ flat speed: it inherits the [__] of both figures.",
    ),
    "slope_cost_curve": (
        "Walking cost by slope",
        "Measured on Earth without a suit: only its shape relative to flat ground is used.",
    ),
    "mars_gravity": (
        "Surface gravity of Mars",
        "GM / R² with the GM from Konopliv et al. and the project's mean radius. It sets the"
        " bounds of the O₂ interval; it does not change the route.",
    ),
    "crew_size": ("EVA crew", None),
    "autonomy": (
        "Suit autonomy",
        f"EVAs of up to 8 h (6 ± 2 h), plus 1 h of secondary O₂. {LUNAR_ON_MARS}",
    ),
    "autonomy_reserve": ("Autonomy reserve", None),
    "task_time": (
        "Fixed EVA work (not walking)",
        "Stops and sampling at the destination; set per request with `suit.task_h`.",
    ),
    "walkback_reserve": (
        "Reserve when returning to base (point of no return)",
        "Set in the team plan; still needs a source with a DOI. The stricter of this and the"
        " 20 % reserve applies: with 8 h, the 20 % wins.",
    ),
    "max_slope": (
        "Maximum walkable slope",
        f"Walking up, down or across up to 20°; Apollo 15 walked on ~17°. {LUNAR_ON_MARS}",
    ),
    "max_distance": (
        "Maximum distance from base",
        "Emergency walk back if the rover fails, as Apollo astronauts asked for. The Moon"
        " assumes 10 km; on Mars it is still to be defined and untested at 0.38 g. For a"
        " walking-only EVA, Coan (2020) gives 2 km radial.",
    ),
    "max_dose": (
        "Dose limit per EVA",
        "NASA sets no per-EVA limit, only a career limit [V1 4030] and a design limit for a"
        " solar event [V1 4031]. Dose only raises an alert if a limit is requested.",
    ),
    "career_dose_limit": (
        "Career effective dose limit",
        "Below 600 mSv for any age and sex; it covers all missions.",
    ),
    "radiation_rate": (
        "Surface dose equivalent",
        "Curiosity RAD, Gale crater, with an uncertainty of ±0.12 mSv/day.",
    ),
    "solar_event_dose": (
        "Absorbed dose of the solar event scenario",
        "Curiosity RAD, May 20, 2024. Applied in full as the worst case.",
    ),
    "sol_length": ("Length of a sol", None),
    "mars_radius": ("Radius of Mars", None),
    "slope_warning": ("Steep segment warning", None),
    "science_threshold": ("Mineral stop threshold", None),
    "ice_threshold": ("Ice stop threshold", None),
    "stop_gap": ("Minimum spacing between stops", None),
    "min_cell_cost": ("Minimum cost per cell", None),
    "weights_safe": ("Safe mode weights", None),
    "weights_fast": ("Fast mode weights", None),
    "weights_science": ("Science mode weights", None),
    "weights_baseline": ("Baseline (shortest distance) weights", None),
}

# Fuentes y unidades que son texto en español.
TEXT_EN = {
    "Decisión del proyecto": "Project decision",
    "Convención del proyecto (radio medio)": "Project convention (mean radius)",
    "personas": "people",
    "fracción": "fraction",
    "mSv/día": "mSv/day",
    "fracción de la pendiente máxima": "fraction of the maximum slope",
    "índice 0-1": "index 0-1",
    "puntos de la ruta": "route points",
}

# Pesos de los modos: "pendiente 4, riesgo 4, ..." -> "slope 4, hazard 4, ...".
WEIGHT_WORDS_EN = {
    "pendiente": "slope",
    "riesgo": "hazard",
    "inestabilidad": "instability",
    "ciencia": "science",
}

# Cada límite en el mismo orden que LIMITS de assumptions.py. Si cambias LIMITS, cambia esta lista:
# test_every_limit_has_an_english_version lo revisa.
LIMITS_EN = [
    "While a region has synthetic data, its figures do not describe the real terrain of Mars.",
    "EVA duration counts the walk plus fixed work (`task_h`), which is 0 until the team sets a"
    " sourced value. Rest stops are not modeled.",
    "The return uses the same speed as the way out (Tobler at 2 km/h on flat ground). There is no"
    " contingency speed with a DOI source to return faster or slower.",
    "Speed, autonomy, maximum slope and distance from base come from lunar Artemis documents and"
    " are applied to Mars without testing at 0.38 g.",
    "The return is computed along the same path as the way out.",
    "The radiation rate was measured at Gale by Curiosity, not at Jezero, and it varies with the"
    " solar cycle and atmospheric pressure.",
    "The solar event dose is absorbed (mGy) and is not added to the dose equivalent (mSv): the"
    " quality factor of that event is missing. A future event could be larger.",
    "Distances follow an 8-neighbor grid, which overestimates them by up to about 8 %.",
    "The pipeline slope assumes square cells: it loses precision far from the equator.",
    "There are no weather alerts yet: the API does not receive the departure time.",
    "The O₂-by-slope curve was measured on Earth, at 1 g and without a suit: it only gives the"
    " shape. That is why O₂ by slope is given as an interval and not as one figure.",
    "The official O₂ figure is `o2_interval_kg` (walking with the Minetti curve plus fixed work"
    " at the hourly rate). `o2_estimate_kg` is only duration × hourly rate: it is a reference"
    " and is not shown in the interface.",
]


def _translate_value(value: float | str | None) -> float | str | None:
    if not isinstance(value, str):
        return value
    for es, en in WEIGHT_WORDS_EN.items():
        value = value.replace(es, en)
    return value


def _translate(p: Assumption) -> Assumption:
    label, note = PARAMETERS_EN.get(p.id, (p.label, p.note))
    return p.model_copy(
        update={
            "label": label,
            "note": note if note is not None else p.note,
            "value": _translate_value(p.value),
            "unit": TEXT_EN.get(p.unit, p.unit) if p.unit else p.unit,
            "source": TEXT_EN.get(p.source, p.source),
        }
    )


def to_english(res: AssumptionsResponse) -> AssumptionsResponse:
    """Misma respuesta con los textos en inglés. Si LIMITS cambia de largo, deja los límites en
    español en vez de emparejarlos mal."""
    limits = LIMITS_EN if len(LIMITS_EN) == len(LIMITS) else res.limits
    return AssumptionsResponse(parameters=[_translate(p) for p in res.parameters], limits=limits)

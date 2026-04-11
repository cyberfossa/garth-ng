from datetime import datetime

from garmin_fit_sdk import Encoder


# FIT message type IDs (from FIT SDK profile)
_FILE_ID = 0
_DEVICE_INFO = 23
_WEIGHT_SCALE = 30
_GENERATOR_MANUFACTURER = "development"
_GENERATOR_PRODUCT = 1
_GENERATOR_SOFTWARE_VERSION = 1.0
_GENERATOR_SERIAL_NUMBER = 0


def build_body_composition(
    weight: float,
    timestamp: datetime,
    *,
    percent_fat: float | None = None,
    percent_hydration: float | None = None,
    muscle_mass: float | None = None,
    bone_mass: float | None = None,
    bmi: float | None = None,
    basal_met: float | None = None,
    active_met: float | None = None,
    metabolic_age: int | None = None,
    physique_rating: int | None = None,
    visceral_fat_mass: float | None = None,
    visceral_fat_rating: int | None = None,
) -> bytes:
    """Build a FIT file with a weight_scale message.

    Args:
        weight: Weight in kilograms.
        timestamp: UTC timestamp for the measurement.
        percent_fat: Body fat percentage.
        percent_hydration: Body hydration percentage.
        muscle_mass: Muscle mass in kilograms.
        bone_mass: Bone mass in kilograms.
        bmi: Body mass index.
        basal_met: Basal metabolic rate in kcal/day.
        active_met: Active metabolic rate in kcal/day.
        metabolic_age: Metabolic age in years.
        physique_rating: Physique rating (uint8, 0-254).
        visceral_fat_mass: Visceral fat mass in kilograms.
        visceral_fat_rating: Visceral fat rating (uint8, 0-254).

    Returns:
        FIT file bytes.
    """
    if weight <= 0 or weight > 655.34:
        raise ValueError(
            f"weight must be between 0 (exclusive) and 655.34 kg, got {weight}"
        )
    if timestamp.tzinfo is None:
        raise ValueError(
            "timestamp must be timezone-aware (got naive datetime)"
        )
    if physique_rating is not None and not 0 <= physique_rating <= 254:
        raise ValueError(
            f"physique_rating must be between 0 and 254, got {physique_rating}"
        )
    if visceral_fat_rating is not None and not 0 <= visceral_fat_rating <= 254:
        raise ValueError(
            f"visceral_fat_rating must be between 0 and 254, "
            f"got {visceral_fat_rating}"
        )
    encoder = Encoder()
    encoder.on_mesg(
        _FILE_ID,
        {
            "type": "weight",
            "manufacturer": _GENERATOR_MANUFACTURER,
            "product": _GENERATOR_PRODUCT,
            "time_created": timestamp,
            "serial_number": _GENERATOR_SERIAL_NUMBER,
        },
    )
    encoder.on_mesg(
        _DEVICE_INFO,
        {
            "device_index": "creator",
            "manufacturer": _GENERATOR_MANUFACTURER,
            "product": _GENERATOR_PRODUCT,
            "software_version": _GENERATOR_SOFTWARE_VERSION,
            "timestamp": timestamp,
        },
    )
    weight_scale: dict[str, datetime | float | int] = {
        "timestamp": timestamp,
        "weight": round(
            weight * 100
        ),  # FIT stores weight in centikilograms (uint16)
    }
    optionals = {
        "percent_fat": percent_fat,
        "percent_hydration": percent_hydration,
        "muscle_mass": muscle_mass,
        "bone_mass": bone_mass,
        "bmi": bmi,
        "basal_met": basal_met,
        "active_met": active_met,
        "metabolic_age": metabolic_age,
        "physique_rating": physique_rating,
        "visceral_fat_mass": visceral_fat_mass,
        "visceral_fat_rating": visceral_fat_rating,
    }
    weight_scale.update({k: v for k, v in optionals.items() if v is not None})
    encoder.on_mesg(_WEIGHT_SCALE, weight_scale)
    return encoder.close()

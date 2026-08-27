"""
PYRO-SENTRY Real Classifier.

Single source of truth for thermal anomaly classification.
Both the live pipeline and /simulation/run call this — no divergence possible.

Classification categories:
  - INDUSTRIAL_FLARE: Known industrial facility proximity + moderate thermal signature
  - WILDFIRE: High FRP, low NDVI, strong SWIR anomaly
  - PRESCRIBED_BURN: Low FRP, low persistence, controlled pattern
  - FALSE_POSITIVE: High vegetation moisture, low thermal signature
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class EvidenceItem:
    """Single evidence factor supporting the classification."""
    factor: str
    value: str
    impact: str
    weight: float


@dataclass
class ClassificationResult:
    """Output of the classifier."""
    primary_class: str
    confidence: float
    probabilities: Dict[str, float]
    evidence: List[EvidenceItem] = field(default_factory=list)


def classify(
    frp: float,
    brightness: float,
    persistence: int,
    industrial_proximity: float,
    wind_speed: float,
    wind_direction: float,
    ndvi: float,
    nbr: float,
    swir_anomaly: float,
) -> ClassificationResult:
    """
    Classify a thermal anomaly detection based on feature vector.

    This function is the SINGLE SOURCE OF TRUTH for classification logic.
    Both live pipeline processing and simulation/run call this function.

    Args:
        frp: Fire Radiative Power in MW
        brightness: Brightness temperature in Kelvin
        persistence: Consecutive sensor detection count
        industrial_proximity: Distance in km to nearest industrial facility
        wind_speed: Wind speed in km/h
        wind_direction: Wind azimuth (0-360 degrees)
        ndvi: Normalized Difference Vegetation Index (-1.0 to 1.0)
        nbr: Normalized Burn Ratio (-1.0 to 1.0)
        swir_anomaly: Short-Wave Infrared anomaly index

    Returns:
        ClassificationResult with primary_class, confidence, probabilities, and evidence.
    """
    evidence_items: List[EvidenceItem] = []

    # ─── Rule-based classification (evidence-first approach) ─────────────

    if industrial_proximity <= 0.8 and frp < 80.0:
        # Strong industrial proximity signal
        primary_class = "INDUSTRIAL_FLARE"
        confidence = round(min(0.98, 0.75 + (0.8 - industrial_proximity) * 0.25), 2)
        evidence_items.append(EvidenceItem(
            factor="Industrial Proximity",
            value=f"{industrial_proximity} km",
            impact="High spatial alignment with industrial facility / flare stack",
            weight=0.45,
        ))

    elif ndvi > 0.65 and brightness < 315.0 and frp < 30.0:
        # High vegetation moisture + low thermal = likely false positive
        primary_class = "FALSE_POSITIVE"
        confidence = 0.85
        evidence_items.append(EvidenceItem(
            factor="High Vegetation Moisture & Low Temp",
            value=f"NDVI={ndvi}, Temp={brightness}K",
            impact="Thermal signal likely caused by solar reflectance or sensor artifact",
            weight=0.50,
        ))

    elif frp < 40.0 and persistence <= 2 and wind_speed < 15.0 and nbr > 0.1:
        # Controlled, low-intensity burn pattern
        primary_class = "PRESCRIBED_BURN"
        confidence = 0.78
        evidence_items.append(EvidenceItem(
            factor="Controlled Thermal Signature",
            value=f"FRP={frp} MW, NBR={nbr}",
            impact="Low rate of spread with moderate localized heat signature",
            weight=0.35,
        ))

    else:
        # Default: uncontrolled thermal event
        primary_class = "WILDFIRE"
        conf_score = 0.70 + (min(150.0, frp) / 500.0) + (swir_anomaly * 0.04)
        confidence = round(min(0.99, conf_score), 2)
        evidence_items.append(EvidenceItem(
            factor="High Thermal Intensity (FRP)",
            value=f"{frp} MW",
            impact="Substantial convective energy detected",
            weight=0.35,
        ))

    # ─── Common supporting evidence ──────────────────────────────────────

    if ndvi < 0.25:
        evidence_items.append(EvidenceItem(
            factor="Dry Vegetation Fuel (NDVI)",
            value=f"{ndvi}",
            impact="Low moisture fuel bed increases ignition and spread potential",
            weight=0.25,
        ))

    if swir_anomaly > 2.0:
        evidence_items.append(EvidenceItem(
            factor="SWIR Infrared Anomaly",
            value=f"{swir_anomaly}",
            impact="Strong shortwave infrared reflection confirms active combustion",
            weight=0.20,
        ))

    if wind_speed > 20.0:
        evidence_items.append(EvidenceItem(
            factor="Elevated Wind Velocity",
            value=f"{wind_speed} km/h",
            impact="High wind accelerates forward fire line advancement",
            weight=0.20,
        ))

    # ─── Compute probability distribution ────────────────────────────────

    probabilities = _compute_probabilities(primary_class, confidence)

    return ClassificationResult(
        primary_class=primary_class,
        confidence=confidence,
        probabilities=probabilities,
        evidence=evidence_items,
    )


def _compute_probabilities(primary_class: str, confidence: float) -> Dict[str, float]:
    """Generate a normalized probability distribution across all classes."""
    classes = ["WILDFIRE", "INDUSTRIAL_FLARE", "PRESCRIBED_BURN", "FALSE_POSITIVE"]
    remaining = round(1.0 - confidence, 2)

    probabilities = {}
    for cls in classes:
        if cls == primary_class:
            probabilities[cls] = confidence
        else:
            probabilities[cls] = round(remaining / (len(classes) - 1), 2)

    # Normalize to ensure sum == 1.0
    total = sum(probabilities.values())
    if total != 1.0:
        diff = round(1.0 - total, 4)
        probabilities[primary_class] = round(probabilities[primary_class] + diff, 4)

    return probabilities

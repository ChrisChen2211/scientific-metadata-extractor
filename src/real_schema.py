"""Shared schema for real-paper metadata extraction and evaluation."""

from typing import Optional

from pydantic import BaseModel, Field


REAL_METADATA_FIELDS = [
    "study_design",
    "population",
    "sample_size",
    "intervention_or_exposure",
    "biospecimen",
    "measurement_method",
    "duration_or_timepoints",
]


class RealScientificMetadata(BaseModel):
    """Metadata that must be supported directly by the supplied excerpt."""

    study_design: Optional[str] = Field(
        description="Study design explicitly stated in the excerpt, otherwise null."
    )
    population: Optional[str] = Field(
        description="Participant population explicitly stated in the excerpt, otherwise null."
    )
    sample_size: Optional[int] = Field(
        description="Number of participants explicitly stated for the described analysis, otherwise null."
    )
    intervention_or_exposure: Optional[str] = Field(
        description="Intervention, condition, or exposure explicitly stated in the excerpt, otherwise null."
    )
    biospecimen: Optional[str] = Field(
        description="Biological specimen explicitly stated in the excerpt, otherwise null."
    )
    measurement_method: Optional[str] = Field(
        description="Measurement or assay method explicitly stated in the excerpt, otherwise null."
    )
    duration_or_timepoints: Optional[str] = Field(
        description="Study duration or collection timepoints explicitly stated in the excerpt, otherwise null."
    )

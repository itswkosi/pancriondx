from pydantic import BaseModel
from typing import Optional


class Variant(BaseModel):
    gene: str
    variant_id: str
    consequence: Optional[str] = None
    clinvar_classification: Optional[str] = None
    allele_frequency: Optional[float] = None
    predicted_impact: Optional[str] = None

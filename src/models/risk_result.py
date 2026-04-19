from pydantic import BaseModel
from typing import Dict, List


class GeneScore(BaseModel):
    gene: str
    weight: float
    raw_score: float
    normalized_score: float


class RiskResult(BaseModel):
    patient_id: str
    overall_score: float
    gene_scores: List[GeneScore]
    details: Dict[str, float] = {}

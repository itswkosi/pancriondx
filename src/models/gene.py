from pydantic import BaseModel
from typing import Optional, Dict


class Gene(BaseModel):
    gene_symbol: str
    inheritance_pattern: Optional[str] = None
    disease_association: Optional[str] = None
    baseline_weight: float = 1.0
    pathogenicity_multiplier: Dict[str, float] = {}

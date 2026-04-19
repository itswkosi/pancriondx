from typing import Any, Dict, Optional

from ..models.variant import Variant
from ..models.gene import Gene


IMPACT_FACTORS: Dict[str, float] = {
    "high": 1.5,
    "moderate": 1.2,
    "low": 1.0,
    "modifier": 0.8,
}


class MutationWeightCalculator:
    def __init__(self, gene_panel: Dict[str, Any]):
        """gene_panel maps gene_symbol -> Gene object or simple dict"""
        self.gene_panel = gene_panel

    def calculate(self, variant: Variant) -> float:
        """Calculate a final weight for a single variant.

        Formula:
            weight = gene.baseline_weight * pathogenicity_multiplier * impact_factor
        """
        gene_obj = self.gene_panel.get(variant.gene)
        if not gene_obj:
            return 0.0

        # support both pydantic models and dicts
        if hasattr(gene_obj, "baseline_weight"):
            baseline = gene_obj.baseline_weight
            mult_map = gene_obj.pathogenicity_multiplier
        else:
            baseline = gene_obj.get("baseline_weight", 1.0)
            mult_map = gene_obj.get("pathogenicity_multiplier", {})

        # lookup pathogenicity multiplier
        mult = 1.0
        if variant.clinvar_classification:
            mult = mult_map.get(variant.clinvar_classification, 1.0)

        # impact factor
        impact = 1.0
        if variant.predicted_impact:
            impact = IMPACT_FACTORS.get(variant.predicted_impact.lower(), 1.0)

        return baseline * mult * impact

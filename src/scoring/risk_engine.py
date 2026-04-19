from math import log
from pathlib import Path
from typing import List, Dict, Any

from ..data.gene_panel_loader import GenePanelLoader
from ..models.variant import Variant
from ..models.risk_result import RiskResult

# impact modifier lookup table
IMPACT_MODIFIERS: Dict[str, float] = {
    "frameshift": 3.0,
    "nonsense": 3.0,
    "splice_site": 2.5,
    "missense": 1.5,
    "synonymous": 0.5,
}


class RiskEngine:
    def __init__(self, gene_panel: Dict[str, Any]):
        """gene_panel: mapping gene_symbol->metadata including baseline weight & multipliers"""
        self.gene_panel = {k.upper(): v for k, v in gene_panel.items()}

    def calculate(self, patient_id: str, annotated_variants: List[Variant]) -> Dict[str, Any]:
        """Compute risk score and classification from annotated variants.

        Returns a dictionary with:
            score: float
            risk_level: str
            variant_contributions: list of (variant_id, score)
        """
        total = 0.0
        contributions = []

        for var in annotated_variants:
            gene_meta = self.gene_panel.get(var.gene.upper())
            if not gene_meta:
                continue
            baseline = gene_meta.get("baseline_weight", 1.0)
            mult = 1.0
            if var.clinvar_classification:
                mult = gene_meta.get("pathogenicity_multiplier", {}).get(
                    var.clinvar_classification, 1.0
                )
            impact_key = (var.consequence or var.predicted_impact or "").lower()
            impact_mod = IMPACT_MODIFIERS.get(impact_key, 1.0)

            var_score = baseline * mult * impact_mod
            total += var_score
            contributions.append(
                {
                    "variant_id": var.variant_id,
                    "gene": var.gene,
                    "disease": gene_meta.get("disease_association"),
                    "score": var_score,
                }
            )

        normalized = log(1 + total)
        if normalized <= 1:
            level = "Low"
        elif normalized <= 2:
            level = "Moderate"
        elif normalized <= 3:
            level = "Elevated"
        else:
            level = "High"

        return {"score": total, "normalized": normalized, "risk_level": level, "variant_contributions": contributions}


def calculate_risk(variants: List[Variant]) -> Dict[str, Any]:
    """Calculate a simplified CLI-friendly risk summary for a list of variants."""
    panel_path = Path(__file__).resolve().parent.parent / "data" / "gene_panel.json"
    loader = GenePanelLoader(panel_path)
    panel_map = {key: value.model_dump() for key, value in loader.as_dict().items()}

    engine = RiskEngine(panel_map)
    result = engine.calculate("cli-user", variants)

    gene_scores: Dict[str, float] = {}
    for contribution in result["variant_contributions"]:
        gene = contribution["gene"]
        gene_scores[gene] = gene_scores.get(gene, 0.0) + contribution["score"]

    top_genes = [
        gene
        for gene, _ in sorted(gene_scores.items(), key=lambda item: item[1], reverse=True)[:5]
    ]
    classification = (
        "Late-stage likely"
        if result["risk_level"] in {"Elevated", "High"}
        else "Early-stage likely"
    )

    return {
        "score": float(result["score"]),
        "classification": classification,
        "top_genes": top_genes,
    }

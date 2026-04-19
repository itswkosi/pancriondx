from typing import List

from ..models.risk_result import GeneScore
from ..models.variant import Variant


def compute_gene_scores(variants: List[Variant], weight_map: dict) -> List[GeneScore]:
    """Aggregate variant weights by gene and produce GeneScore objects."""
    scores: dict[str, float] = {}
    for v in variants:
        gene = v.gene
        score = weight_map.get(v.clinvar_classification, 0.0) if v.clinvar_classification else 0.0
        scores[gene] = scores.get(gene, 0.0) + score

    return [GeneScore(gene=g, weight=s, raw_score=s, normalized_score=0.0) for g, s in scores.items()]

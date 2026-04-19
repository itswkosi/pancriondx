from typing import List, Dict, Any, Tuple



def generate_interpretation(
    normalized_score: float,
    contributions: List[Dict[str, Any]],
    gene_diseases: Dict[str, str],
    risk_level: str,
) -> Tuple[Dict[str, Any], str]:
    """Create both JSON structure and human-readable report text.

    `gene_diseases` maps gene symbols to disease associations.

    Returns a tuple (json_obj, narrative).
    """
    # build list of high-impact variants (score above some threshold)
    high_impact = [c for c in contributions if c.get("score", 0) > 1]
    diseases = sorted({gene_diseases.get(c.get("gene"), "") for c in high_impact})

    json_report = {
        "normalized_score": normalized_score,
        "risk_level": risk_level,
        "variant_contributions": contributions,
        "high_impact_variants": high_impact,
        "associated_diseases": diseases,
    }

    # build narrative
    parts: List[str] = []
    if high_impact:
        for v in high_impact:
            g = v.get("gene")
            score = v.get("score")
            disease = gene_diseases.get(g, "")
            parts.append(
                f"Detected pathogenic {g} variant (score {score:.2f}) associated with {disease}."
            )
    parts.append(f"{risk_level} genomic risk detected.")
    narrative = " ".join(parts)

    # include generic follow-up suggestions
    json_report["suggested_follow_up"] = [
        "Confirm variants with orthogonal testing.",
        "Consult genetics specialist for additional counseling.",
    ]
    narrative += " Suggested follow-up: confirm variants with orthogonal testing and consult genetics specialist."

    return json_report, narrative
